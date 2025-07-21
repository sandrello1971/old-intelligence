import os
import requests
import psycopg2

# --- CONFIG --- #
CRM_API_KEY = os.getenv("CRM_API_KEY") or "INSERISCI_API_KEY"
CRM_USERNAME = os.getenv("CRM_USERNAME") or "INSERISCI_USERNAME"
CRM_PASSWORD = os.getenv("CRM_PASSWORD") or "INSERISCI_PASSWORD"
CRM_BASE_URL = "https://api.crmincloud.it/api/v1"
DB_URL = os.getenv("DATABASE_URL") or "postgresql://postgres:postgres@localhost:5432/intelligence_db"

# --- CRM AUTH --- #
def get_crm_token():
    res = requests.post(
        f"{CRM_BASE_URL}/Auth/Login",
        json={"grant_type": "password", "username": CRM_USERNAME, "password": CRM_PASSWORD},
        headers={"WebApiKey": CRM_API_KEY, "Content-Type": "application/json"}
    )
    res.raise_for_status()
    return res.json()["access_token"]

# --- CRM FETCH --- #
def fetch_all_categories(token):
    headers = {"Authorization": f"Bearer {token}", "WebApiKey": CRM_API_KEY}
    res = requests.get(f"{CRM_BASE_URL}/OpportunityCategory/", headers=headers)
    res.raise_for_status()
    return res.json()

def fetch_category_detail(token, cid):
    headers = {"Authorization": f"Bearer {token}", "WebApiKey": CRM_API_KEY}
    res = requests.get(f"{CRM_BASE_URL}/OpportunityCategory/{cid}/GetFull", headers=headers)
    res.raise_for_status()
    return res.json()

# --- DB INSERT --- #
def upsert_categories_to_db(categories):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    for cat in categories:
        cur.execute("""
            INSERT INTO opportunity_categories (id, code, description, created_date, last_modified_date)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                code = EXCLUDED.code,
                description = EXCLUDED.description,
                created_date = EXCLUDED.created_date,
                last_modified_date = EXCLUDED.last_modified_date;
        """, (
            cat["id"],
            cat.get("code", ""),
            cat.get("description", ""),
            cat.get("createdDate"),
            cat.get("lastModifiedDate"),
        ))
    conn.commit()
    cur.close()
    conn.close()

# --- MAIN --- #
def main():
    token = get_crm_token()
    ids = fetch_all_categories(token)
    print(f"🔍 Trovati {len(ids)} ID categoria")

    categories = []
    for cid in ids:
        try:
            data = fetch_category_detail(token, cid)
            categories.append(data)
            print(f"✅ {cid}: {data['description']}")
        except Exception as e:
            print(f"❌ Errore {cid}: {e}")

    upsert_categories_to_db(categories)
    print("✅ Inserimento completato nel database.")

if __name__ == "__main__":
    main()

