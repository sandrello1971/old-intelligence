# app/routes/activity.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from integrations.crm_incloud.sync import sync_single_activity

router = APIRouter(prefix="/api/activities", tags=["activities"])

@router.post("/{activity_id}/sync")
def sync_activity(activity_id: int, db: Session = Depends(get_db)):
    """
    Sincronizza una singola attività dal CRM nel database locale.
    """
    try:
        activity = sync_single_activity(activity_id, db)
        if not activity:
            raise HTTPException(status_code=404, detail="Attività non trovata o errore nella sync")
        return {"status": "ok", "activity_id": activity.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
