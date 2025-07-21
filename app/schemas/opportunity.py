# app/schemas/opportunity.py

from pydantic import BaseModel
from typing import List

class OpportunityCreate(BaseModel):
    title: str
    crossId: int
    ownerId: int | None = None
    description: str
    phase: int
    category: int
    status: int
    salesPersons: List[int]
    budget: int
    amount: int
