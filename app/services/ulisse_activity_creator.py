import os
import requests
from integrations.crm_incloud.sync import get_crm_token

CRM_API_KEY = os.getenv("CRM_API_KEY")
CRM_BASE_URL = "https://app.crmincloud.it/api/v1"

def create_ulisse_crm_activity(data: dict) -> int:
    token = get_crm_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "WebApiKey": CRM_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "customer_name": data["customer_name"],
        "description": data["description"],
        "sub_type_id": data.get("sub_type_id", 63705),
        "accompagnato_da": data.get("accompagnato_da"),
        "accompagnato_da_nome": data.get("accompagnato_da_nome"),
        "title": f"I24 per {data['customer_name']}",
        "status": "aperta",
        "priority": "bassa"
    }

    res = requests.post(f"{CRM_BASE_URL}/activities", json=payload, headers=headers)
    res.raise_for_status()
    return res.json()["id"]
