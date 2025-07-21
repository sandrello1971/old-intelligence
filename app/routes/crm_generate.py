# app/routes/crm_generate.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.crm_generator import generate_opportunities_for_activity

router = APIRouter(prefix="/crm", tags=["CRM"])

@router.post("/generate/{activity_id}")
def generate_for_activity(activity_id: int, db: Session = Depends(get_db)):
    """
    Genera opportunità CRM per una specifica attività (Incarico 24 mesi),
    insieme a ticket e task derivati.
    """
    try:
        result = generate_opportunities_for_activity(activity_id, db)
        return {"status": "success", "details": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
