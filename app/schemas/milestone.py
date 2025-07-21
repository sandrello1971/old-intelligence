from pydantic import BaseModel
from typing import Optional

class MilestoneBase(BaseModel):
    name: str
    project_type: str
    order: int
    sla_days: Optional[int] = 5
    warning_days: Optional[int] = 2
    escalation_days: Optional[int] = 3

class MilestoneCreateSchema(MilestoneBase):
    pass

class MilestoneUpdateSchema(BaseModel):
    name: Optional[str] = None
    project_type: Optional[str] = None
    order: Optional[int] = None
    sla_days: Optional[int] = None
    warning_days: Optional[int] = None
    escalation_days: Optional[int] = None

class MilestoneSchema(MilestoneBase):
    id: int
    
    class Config:
        from_attributes = True  # se usi Pydantic v2
