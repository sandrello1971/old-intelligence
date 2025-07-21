from fastapi import APIRouter
from integrations.crm_incloud.sync import sync_from_crm_since_json, sync_single_activity
import threading
import logging
from app.services.crm_parser import extract_opportunities_from_description

router = APIRouter()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@router.get("/crm/sync", tags=["CRM"])
def sync_crm_data():
    def run_sync():
        logger.info("🟡 Sync CRM avviato in background...")
        try:
            result = sync_from_crm_since_json()
            logger.info(f"✅ Sync completato: {result}")
        except Exception as e:
            logger.error(f"❌ Errore sync CRM: {e}")

    thread = threading.Thread(target=run_sync)
    thread.start()

    return {
        "status": "started",
        "message": "🔄 Sync avviato. Controlla i log per lo stato."
    }

@router.get("/crm/sync/{activity_id}", tags=["CRM"])
def sync_crm_activity(activity_id: int):
    """
    Sincronizza una singola attività dal CRM tramite ID.
    """
    try:
        result = sync_single_activity(activity_id)
        return {
            "status": "success",
            "activity_id": activity_id,
            "details": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@router.post("/crm/create-activity", tags=["CRM"])
def create_activity(payload: dict):
    """
    Crea una nuova attività su CRM InCloud a partire da un payload JSON.
    """
    from integrations.crm_incloud.create import create_crm_activity  # ⚡ chiamata diretta

    try:
        result = create_crm_activity(payload)
        return {"status": "success", "crm_response": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/crm/parse-opportunities", tags=["CRM"])
def parse_opportunities(payload: dict):
    """
    Estrae opportunità da una descrizione.
    """
    description = payload.get("description", "")
    opportunities = extract_opportunities_from_description(description)
    return {"opportunities": opportunities}
