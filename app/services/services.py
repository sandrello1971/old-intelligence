
# app/routes/services.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.phase_template import PhaseTemplate

router = APIRouter(tags=["services"])

@router.get("/services")
def list_services(db: Session = Depends(get_db)):
    results = db.query(PhaseTemplate.type).distinct().all()
    return [r[0] for r in results if r[0]]

