# app/routes/phase_templates.py (esteso)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.phase_template import PhaseTemplate
from app.schemas.phase_template import PhaseTemplateSchema, PhaseTemplateAssociateSchema

router = APIRouter(tags=["phase_templates"])

@router.get("/phase-templates/codes", response_model=List[str])
def list_codes(db: Session = Depends(get_db)):
    codes = db.query(PhaseTemplate.code).distinct().all()
    return [c[0] for c in codes]

@router.get("/phase-templates/types/{code}", response_model=List[str])
def list_types(code: str, db: Session = Depends(get_db)):
    types = db.query(PhaseTemplate.type).filter(PhaseTemplate.code == code).distinct().all()
    return [t[0] for t in types]

@router.get("/phase-templates/descriptions/{code}/{type}", response_model=List[PhaseTemplateSchema])
def list_descriptions(code: str, type: str, db: Session = Depends(get_db)):
    descriptions = db.query(PhaseTemplate).filter(
        PhaseTemplate.code == code,
        PhaseTemplate.type == type
    ).all()
    return descriptions

@router.patch("/phase-templates/{phase_id}/associate-milestone", response_model=PhaseTemplateSchema)
def associate_milestone(phase_id: int, body: PhaseTemplateAssociateSchema, db: Session = Depends(get_db)):
    phase = db.query(PhaseTemplate).filter(PhaseTemplate.id == phase_id).first()
    if not phase:
        raise HTTPException(status_code=404, detail="PhaseTemplate non trovato")
    phase.milestone_id = body.milestone_id
    db.commit()
    db.refresh(phase)
    return phase

# ✅ Nuova API: Tabella riassuntiva con milestone associate
@router.get("/phase-templates/with-milestone", response_model=List[PhaseTemplateSchema])
def list_phases_with_milestone(db: Session = Depends(get_db)):
    phases = db.query(PhaseTemplate).all()
    return phases

# ✅ NUOVA API: Lista delle associazioni fase-milestone
@router.get("/phase-templates/associations", response_model=List[PhaseTemplateSchema])
def list_associations(db: Session = Depends(get_db)):
    return db.query(PhaseTemplate).all()
