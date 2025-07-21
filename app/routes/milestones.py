from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.milestone import Milestone
from app.schemas.milestone import MilestoneSchema, MilestoneCreateSchema, MilestoneUpdateSchema

router = APIRouter()

@router.get("/milestones", response_model=List[MilestoneSchema])
def list_milestones(db: Session = Depends(get_db)):
    return db.query(Milestone).order_by(Milestone.project_type, Milestone.order).all()

@router.post("/milestones", response_model=MilestoneSchema)
def create_milestone(milestone: MilestoneCreateSchema, db: Session = Depends(get_db)):
    db_milestone = Milestone(**milestone.dict())
    db.add(db_milestone)
    db.commit()
    db.refresh(db_milestone)
    return db_milestone

@router.delete("/milestones/{milestone_id}", status_code=204)
def delete_milestone(milestone_id: int, db: Session = Depends(get_db)):
    milestone = db.query(Milestone).get(milestone_id)
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    db.delete(milestone)
    db.commit()
    return

@router.patch("/milestones/{milestone_id}", response_model=MilestoneSchema)
def update_milestone(milestone_id: int, update_data: MilestoneUpdateSchema, db: Session = Depends(get_db)):
    print(f"🔧 DEBUG: Updating milestone {milestone_id} with data: {update_data.dict(exclude_unset=True)}")
    
    milestone = db.query(Milestone).get(milestone_id)
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    
    print(f"🔧 DEBUG: Before update - sla_days: {milestone.sla_days}")
    
    try:
        for key, value in update_data.dict(exclude_unset=True).items():
            print(f"🔧 DEBUG: Setting {key} = {value}")
            setattr(milestone, key, value)
        
        print(f"🔧 DEBUG: After setattr - sla_days: {milestone.sla_days}")
        
        db.commit()
        print("🔧 DEBUG: Commit executed")
        
        db.refresh(milestone)
        print(f"🔧 DEBUG: After refresh - sla_days: {milestone.sla_days}")
        
        return milestone
    except Exception as e:
        print(f"❌ DEBUG ERROR: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

