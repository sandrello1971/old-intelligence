from typing import List, Optional
from pydantic import BaseModel

class TaskM24Schema(BaseModel):
    id: int
    title: str
    status: str
    priority: str
    children: List["TaskM24Schema"] = []

    class Config:
        orm_mode = True

TaskM24Schema.update_forward_refs()

class MilestoneSchema(BaseModel):
    id: int
    title: str
    type: str
    status: str
    priority: str
    gtd_type: str
    tasks: List[TaskM24Schema] = []
    children: List[TaskM24Schema] = []

    class Config:
        orm_mode = True

class TicketM24Schema(BaseModel):
    id: int
    ticket_code: str
    title: str
    status: str
    priority: str
    type: str
    gtd_type: str
    tasks: List = []
    children: List = []

    class Config:
        orm_mode = True

class ActivityTreeM24Schema(BaseModel):
    id: int
    description: str
    status: str
    tickets: List[TicketM24Schema]
    customer_name: Optional[str] = None  # 👈 AGGIUNGI QUESTO CAMPO

    class Config:
        orm_mode = True
