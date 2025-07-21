import os
import time
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models.company import Company

# ========== CONFIG ==========
load_dotenv(dotenv_path="/app/.env")

CRM_BASE_URL = os.getenv("CRM_BASE_URL", "https://api.crmincloud.it/api/v1")
CRM_USERNAME = os.getenv("CRM_USERNAME")
CRM_PASSWORD = os.getenv("CRM_PASSWORD")
CRM_API_KEY = os.getenv("CRM_API_KEY")

DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{DB_HOST}:5432/{os.getenv('POSTGRES_DB')}"

SLEEP_BETWEEN_CALLS = 2.1

# ========== DB SETUP ==========
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

# ========== AUTENTICAZIONE ==========
def get_crm_token():
    url = f"{CRM_BASE_URL}/Auth/Login"
    payload = {
        "grant_type": "password",
        "userName": CRM_USERNAME,
        "password": CRM_PASSWORD
    }
    headers = {
        "WebApiKey": CRM_API_KEY,
        "Content-Type": "application/json"
    }

    res = requests.post(url, json=payload, headers=headers)
    res.raise_for_status()
    return res.json()["access_token"]

def get_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "WebApiKey": CRM_API_KEY
    }

# ========== API CALLS ==========
def get_all_crm_company_ids(headers):
    url = f"{CRM_BASE_URL}/Company"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()

    if not isinstance(data, list):
        print(f"🛑 Risposta inattesa dal CRM: {type(data)} con contenuto {str(data)[:500]}")
        return []

    return [str(cid) for cid in data if isinstance(cid, int)]

def get_crm_company_by_id(company_id, headers):
    url = f"{CRM_BASE_URL}/Company/{company_id}/GetFull"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

# ========== DB READ ==========
def get_all_db_company_ids():
    print("📥 Estrazione aziende dal DB...")
    result = session.execute(text("SELECT id FROM companies"))
    return {str(r[0]) for r in result.fetchall()}

# ========== SYNC ==========
def sync_crm_companies(db_session, crm_ids, headers, existing_ids):
    inserted = 0
    for index, crm_id in enumerate(crm_ids):
        exists = db_session.execute(
            text("SELECT 1 FROM companies WHERE id::text = :id LIMIT 1"),
            {"id": str(crm_id)}
        ).scalar()

        if exists:
            continue

        data = get_crm_company_by_id(crm_id, headers)
        if not data:
            print(f"⚠️ Azienda ID {crm_id} non trovata.")
            continue

        new_company = Company(
            id=crm_id,
            nome=data.get("companyName") or "N/A",
            partita_iva=data.get("vatId") or f"NO-PIVA-{crm_id}",
            address=data.get("address") or "N/A",
            sector=str(data.get("anagraphicIndustryId") or "")
        )
        db_session.merge(new_company)
        db_session.commit()
        inserted += 1

        print(f"⬇️ {index + 1}/{len(crm_ids)} azienda processata...")
        time.sleep(SLEEP_BETWEEN_CALLS)

    print(f"\n🌟 Inserite {inserted} aziende mancanti nel DB.")

# ========== MAIN ==========
if __name__ == "__main__":
    print("🚀 Avvio sincronizzazione aziende CRM ↔ DB")

    try:
        token = get_crm_token()
        headers = get_headers(token)

        crm_ids = get_all_crm_company_ids(headers)
        db_ids = get_all_db_company_ids()

        print("\n📍 Verifica aziende non presenti nel DB:")
        sync_crm_companies(session, crm_ids, headers, db_ids)

        print("\n📅 Sincronizzazione completata.")

    except Exception as e:
        print(f"\n❌ Errore durante la sincronizzazione: {e}")
