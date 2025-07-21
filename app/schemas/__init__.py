# app/schemas/activity.py
from pydantic import BaseModel
from typing import Optional

class ActivitySchema(BaseModel):
    id: int
    description: Optional[str]
    accompagnato_da: Optional[str]
    due_date: Optional[str]
    priority: Optional[str]
    status: Optional[str]

    class Config:
        orm_mode = True
