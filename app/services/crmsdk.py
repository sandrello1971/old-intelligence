from typing import Optional
from sqlalchemy.orm import Session
import os
import requests
from integrations.crm_incloud.sync import get_crm_token
from sqlalchemy import func
from app.models.company import Company

CRM_API_KEY = os.getenv("CRM_API_KEY")
CRM_BASE_URL = "https://api.crmincloud.it/api/v1"


def create_crm_activity(data: dict) -> int:
    """
    Crea un'attività Ulisse nel CRM e restituisce l'ID creato.
    """
    token = get_crm_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "WebApiKey": CRM_API_KEY,
        "Content-Type": "application/json"
    }

    # Costruzione payload con casting sicuro ai tipi corretti
    payload = {
        "subject": data.get("subject"),
        "title": f"Incarico 24 Mesi - {data.get('customer_name', 'N/A')}",
        "description": data.get("description"),
        "sub_type_id": int(data.get("subTypeId", 63705)),
        "status": "aperta",
        "priority": int(data.get("priority", 0)),
        "ownerId": int(data.get("ownerId")),
        "companyId": int(data.get("companyId")),
        "type": int(data.get("type", 7)),
        "activityDate": data.get("activityDate"),
        "activityEndDate": data.get("activityEndDate"),
        "idCompanion": int(data.get("idCompanion"))
    }

    url = f"{CRM_BASE_URL}/Activity/CreateOrUpdate"
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        response_data = response.json()

        # 👉 Log completo della risposta
        print(">>> JSON completo risposta CRM:", response_data)

        if isinstance(response_data, int):
            return response_data
        elif isinstance(response_data, dict) and "id" in response_data:
            return response_data["id"]
        else:
            raise ValueError(f"Risposta CRM non contiene un ID valido: {response_data}")
    except requests.HTTPError as http_err:
        raise RuntimeError(f"HTTPError creazione attività: {http_err}\nRisposta: {response.text}") from http_err
    except Exception as e:
        raise RuntimeError(f"Errore generico creazione attività: {e}") from e


from sqlalchemy import text

def get_company_id_by_name(company_name: str, db: Session) -> Optional[int]:
    """Trova company_id con fuzzy search - ENHANCED VERSION"""
    if not company_name or not company_name.strip():
        print(f"[FUZZY] ❌ Empty company name")
        return None
    
    company_name = company_name.strip()
    print(f"[FUZZY] 🔍 Searching for: '{company_name}'")
    
    try:
        # Step 1: Exact match (case insensitive)
        exact = db.execute(
            text("SELECT id FROM companies WHERE LOWER(nome) = LOWER(:name)"),
            {"name": company_name}
        ).fetchone()
        
        if exact:
            print(f"[FUZZY] ✅ EXACT MATCH found: company_id={exact[0]}")
            return exact[0]
        
        # Step 2: Fuzzy search with pg_trgm
        print(f"[FUZZY] 🔍 No exact match, trying fuzzy search...")
        fuzzy = db.execute(
            text("""
                SELECT id, nome, similarity(nome, :name) as score
                FROM companies 
                WHERE similarity(nome, :name) > 0.3
                ORDER BY score DESC LIMIT 1
            """),
            {"name": company_name}
        ).fetchone()
        
        if fuzzy:
            company_id, matched_name, score = fuzzy
            print(f"[FUZZY] 🎯 FUZZY MATCH: '{company_name}' → '{matched_name}' (score: {score:.3f})")
            
            if score >= 0.4:  # Accept threshold
                print(f"[FUZZY] ✅ ACCEPTED (score >= 0.4)")
                return company_id
            else:
                print(f"[FUZZY] ⚠️ REJECTED (score {score:.3f} < 0.4)")
                return None
        
        print(f"[FUZZY] ❌ NO MATCH found for: '{company_name}'")
        return None
        
    except Exception as e:
        print(f"[FUZZY] 💥 DATABASE ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None