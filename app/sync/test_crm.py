import os
import requests
from dotenv import load_dotenv

# ===== LOAD CONFIG =====
load_dotenv("/app/.env")

CRM_BASE_URL = os.getenv("CRM_BASE_URL", "https://api.crmincloud.it/api/v1")
CRM_API_KEY = os.getenv("CRM_API_KEY")
CRM_ACCESS_TOKEN = os.getenv("CRM_ACCESS_TOKEN")  # usa un token valido

HEADERS = {
    "Authorization": f"Bearer {CRM_ACCESS_TOKEN}",
    "WebApiKey": CRM_API_KEY,
    "Content-Type": "application/json"
}


def test_get_company_all():
    print("\n🔍 Test GET /Company/All")
    url = f"{CRM_BASE_URL}/Company/All"
    try:
        res = requests.get(url, headers=HEADERS)
        print(f"Status: {res.status_code}, Lunghezza risposta: {len(res.text)}")
        print(res.json()[:3])
    except Exception as e:
        print(f"Errore: {e}")


def test_post_search_advanced():
    print("\n🔍 Test POST /Company/SearchAdvanced")
    url = f"{CRM_BASE_URL}/Company/SearchAdvanced"
    payload = {
        "Page": 1,
        "PageSize": 100
    }
    try:
        res = requests.post(url, json=payload, headers=HEADERS)
        print(f"Status: {res.status_code}, Lunghezza risposta: {len(res.text)}")
        if res.ok:
            data = res.json()
            print(f"Items trovati: {len(data.get('Items', []))}")
            print(data.get("Items", [])[:3])
    except Exception as e:
        print(f"Errore: {e}")


if __name__ == "__main__":
    test_get_company_all()
    test_post_search_advanced()
