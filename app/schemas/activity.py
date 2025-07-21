# app/schemas/activity.py
from pydantic import BaseModel, Field
from typing import List
from typing import Optional


class TaskTreeSchema(BaseModel):
    id: int
    title: str
    status: str
    priority: str
    children: List["TaskTreeSchema"] = []  # 💥 aggiunto

    class Config:
        from_attributes = True  # per Pydantic v2


class TicketTreeSchema(BaseModel):
    id: int
    ticket_code: str
    title: str
    status: str
    priority: str
    gtd_type: str
    tasks: List[TaskTreeSchema]
    children: List['TicketTreeSchema']  # forward reference

class ActivitySchema(BaseModel):
    id: int
    description: str | None
    status: str | None
    priority: str | None
    due_date: str | None
    owner_name: str | None
    accompagnato_da: str | None
    company_name: str | None     # 👈 deve esserci
    account_name: str | None     # 👈 deve esserci

    class Config:
        orm_mode = True

class ActivityTreeSchema(BaseModel):
    id: int
    description: str
    status: str
    tickets: List[TicketTreeSchema]


# Resolving the forward reference
TicketTreeSchema.update_forward_refs()
TaskTreeSchema.update_forward_refs()  # 💥 questa mancava!
