from pydantic import BaseModel
from typing import Optional

class PhaseTemplateBase(BaseModel):
    code: str
    type: str
    description: str

class PhaseTemplateSchema(PhaseTemplateBase):
    id: int
    milestone_id: Optional[int] = None
    order: Optional[int] = None
    parent_id: Optional[int] = None
    milestone_name: Optional[str] = None

    class Config:
        from_attributes = True

class PhaseTemplateAssociateSchema(BaseModel):
    milestone_id: int
    order: Optional[int] = None
    parent_id: Optional[int] = None

class PhaseTemplateCreateSchema(BaseModel):
    code: str
    type: str
    description: str
    order: Optional[int] = None
    parent_id: Optional[int] = None
    milestone_id: Optional[int] = None

class PhaseTemplateUpdate(BaseModel):
    code: Optional[str]
    type: Optional[str]
    description: Optional[str]
    milestone_id: Optional[int]
    order: Optional[int]
