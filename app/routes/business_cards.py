from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db

router = APIRouter(tags=["business_cards"])

@router.get("/business_cards/test")
def test_business_cards():
    return {"message": "Business cards router funziona!", "status": "ok"}

@router.get("/business_cards/stats")
def get_business_cards_stats():
    return {
        "business_cards": {"total": 0, "successful": 0, "avg_confidence": 0, "avg_processing_time": 0},
        "contacts": {"total": 0, "unique_companies": 0, "with_email": 0, "with_phone": 0}
    }

@router.get("/business_cards/contacts") 
def get_contacts():
    return []
