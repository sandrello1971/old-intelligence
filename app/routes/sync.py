# app/routes/sync.py
from fastapi import APIRouter
from integrations.crm_incloud.sync import sync_from_crm_since_json

router = APIRouter(prefix="/sync", tags=["crm-sync"])

@router.post("/crm/activities")
def manual_crm_sync():
    result = sync_from_crm_since_json()
    return {"message": "Sync completato", **result}
