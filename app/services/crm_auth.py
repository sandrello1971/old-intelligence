# app/services/crm_auth.py

import os
import time
import logging
import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

CRM_API_KEY = os.getenv("CRM_API_KEY")
CRM_USERNAME = os.getenv("CRM_USERNAME")
CRM_PASSWORD = os.getenv("CRM_PASSWORD")
CRM_BASE_URL = "https://api.crmincloud.it/api/v1"

def get_crm_token(max_retries=5, base_delay=5):
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

    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 429:
                wait_time = base_delay * (2 ** attempt)
                logger.warning(f"⚠️ CRM rate limit (429). Retry tra {wait_time}s...")
                time.sleep(wait_time)
                continue
            response.raise_for_status()
            return response.json()["access_token"]
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ Errore HTTP nel tentativo {attempt+1}: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(base_delay * (2 ** attempt))
        except Exception as e:
            logger.error(f"❌ Errore generico nel tentativo {attempt+1}: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(base_delay * (2 ** attempt))
