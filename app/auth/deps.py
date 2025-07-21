from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.owner import Owner
from app.auth.google import get_current_user

def get_current_owner_user(db: Session = Depends(get_db)) -> Owner:
    # ✅ Override temporaneo per test
    user = db.query(Owner).filter(Owner.email == "s.andrello@enduser-italia.com").first()
    if not user:
        raise HTTPException(status_code=403, detail="Utente test non trovato nel database")
    return user
