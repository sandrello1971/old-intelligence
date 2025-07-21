# /app/routes/owners.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.owner import Owner

router = APIRouter(tags=["owners"])

@router.get("/owners")
def get_owners(db: Session = Depends(get_db)):
    owners = db.query(Owner).all()
    return [
        {
            "id": o.id,
            "name": o.name,
            "surname": o.surname,
            "email": o.email,
        }
        for o in owners
    ]
