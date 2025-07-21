# app/routes/phase_templates.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.phase_template import PhaseTemplate
from app.models.milestone import Milestone
from app.schemas.phase_template import PhaseTemplateSchema, PhaseTemplateAssociateSchema
from app.schemas.phase_template import PhaseTemplateCreateSchema  # importa il nuovo schema!
from pydantic import BaseModel
	
router = APIRouter(tags=["phase_templates"])

class PhaseTemplateUpdate(BaseModel):
    code: str
    type: str
    description: str
    milestone_id: int | None = None
    order: int | None = None


@router.get("/codes", response_model=List[str])
def list_codes(db: Session = Depends(get_db)):
    codes = db.query(PhaseTemplate.code).distinct().all()
    return [c[0] for c in codes]

@router.get("/types/{code}", response_model=List[str])
def list_types(code: str, db: Session = Depends(get_db)):
    types = db.query(PhaseTemplate.type).filter(PhaseTemplate.code == code).distinct().all()
    return [t[0] for t in types]

@router.get("/descriptions/{code}/{type}", response_model=List[PhaseTemplateSchema])
def list_descriptions(code: str, type: str, db: Session = Depends(get_db)):
    return db.query(PhaseTemplate).filter(
        PhaseTemplate.code == code,
        PhaseTemplate.type == type
    ).all()

@router.patch("/{phase_template_id}/update")
def update_phase_template(phase_template_id: int, phase_data: PhaseTemplateUpdate, db: Session = Depends(get_db)):
    phase = db.query(PhaseTemplate).filter(PhaseTemplate.id == phase_template_id).first()
    if not phase:
        raise HTTPException(status_code=404, detail="PhaseTemplate non trovato")
    
    # Aggiorna i campi ricevuti
    if phase_data.code is not None:
        phase.code = phase_data.code
    if phase_data.type is not None:
        phase.type = phase_data.type
    if phase_data.description is not None:
        phase.description = phase_data.description
    if phase_data.milestone_id is not None:
        phase.milestone_id = phase_data.milestone_id
    if phase_data.order is not None:
        phase.order = phase_data.order

    db.commit()
    db.refresh(phase)
    return {"message": "PhaseTemplate aggiornato correttamente", "phase_template": phase}

@router.get("/associations", response_model=List[PhaseTemplateSchema])
def list_associated_phases(db: Session = Depends(get_db)):
    phases = db.query(PhaseTemplate).filter(PhaseTemplate.milestone_id.isnot(None)).all()
    results = []
    for phase in phases:
        milestone = db.query(Milestone).filter(Milestone.id == phase.milestone_id).first()
        milestone_name = f"{milestone.project_type} - {milestone.name}" if milestone else None
        phase_data = PhaseTemplateSchema.from_orm(phase).dict()
        phase_data["milestone_name"] = milestone_name
        results.append(phase_data)
    return results

@router.post("/phase-templates/", response_model=PhaseTemplateSchema)
def create_phase_template(phase: PhaseTemplateCreateSchema, db: Session = Depends(get_db)):
    new_phase = PhaseTemplate(
        code=phase.code,
        type=phase.type,
        description=phase.description,
        order=phase.order,
        parent_id=phase.parent_id,
        milestone_id=phase.milestone_id,
    )
    db.add(new_phase)
    db.commit()
    db.refresh(new_phase)
    return new_phase

@router.patch("/{id}/update", response_model=dict)
def update_phase_template(id: int, update: PhaseTemplateUpdate, db: Session = Depends(get_db)):
    template = db.query(PhaseTemplate).filter(PhaseTemplate.id == id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Phase template non trovato")

    template.code = update.code
    template.type = update.type
    template.description = update.description
    template.milestone_id = update.milestone_id
    template.order = update.order

    db.commit()
    db.refresh(template)

    return {"message": "Phase template aggiornato"}

