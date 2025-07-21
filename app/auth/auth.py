from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.models.owner import Owner
from app.core.database import get_db
import jwt
import os

JWT_SECRET = os.getenv("JWT_SECRET", "defaultsecret")

def get_current_user(authorization: str = Header(...), db: Session = Depends(get_db)) -> Owner:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token mancante o malformato")
    
    token = authorization[7:]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=403, detail="Token invalido")

        owner = db.query(Owner).filter(Owner.email == email).first()
        if not owner:
            raise HTTPException(status_code=404, detail="Utente non trovato tra gli owner")
        return owner

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token scaduto")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token non valido")
