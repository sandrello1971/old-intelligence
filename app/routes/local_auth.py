from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, constr
from sqlalchemy.orm import Session
import bcrypt
from app.core.database import get_db
from app.models.local_user import LocalUser
from fastapi.responses import JSONResponse
import jwt
import os
from datetime import datetime, timedelta

router = APIRouter(prefix="/logi", tags=["login"])

JWT_SECRET = os.getenv("JWT_SECRET", "defaultsecret")
JWT_EXPIRATION_MINUTES = 60 * 24  # 1 giorno

class LoginInput(BaseModel):
    email: EmailStr
    password: constr(min_length=6)

def create_jwt(user: LocalUser) -> str:
    payload = {
        "sub": user.email,
        "user_id": user.id,
        "role": user.role,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

@router.post("/check")
def check_email(data: LoginInput, db: Session = Depends(get_db)):
    user = db.query(LocalUser).filter(LocalUser.email == data.email).first()
    if not user:
        raise HTTPException(status_code=403, detail="Utente non trovato")

    if user.password is None:
        # Primo accesso per utente creato ma senza password
        hashed_pw = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
        user.password = hashed_pw
        user.must_change_password = False
        db.commit()
        token = create_jwt(user)
        return {
            "message": "✅ Password impostata con successo",
            "mode": "login",
            "token": token,
            "user_id": user.id,
            "email": user.email,
            "role": user.role
        }

    # Se la password esiste, verifica
    if not bcrypt.checkpw(data.password.encode(), user.password.encode()):
        raise HTTPException(status_code=401, detail="❌ Password errata")

    if user.must_change_password:
        return {
            "message": "🔒 Cambio password richiesto",
            "mode": "change_password",
            "email": user.email
        }

    token = create_jwt(user)
    return {
        "message": "✅ Login riuscito",
        "mode": "login",
        "token": token,
        "user_id": user.id,
        "email": user.email,
        "role": user.role
    }


class ChangePasswordInput(BaseModel):
    email: EmailStr
    new_password: constr(min_length=6)

@router.post("/change-password")
def change_password(data: ChangePasswordInput, db: Session = Depends(get_db)):
    user = db.query(LocalUser).filter(LocalUser.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    user.password = bcrypt.hashpw(data.new_password.encode(), bcrypt.gensalt()).decode()
    user.must_change_password = False
    db.commit()

    token = create_jwt(user)
    return {
        "message": "✅ Password cambiata con successo",
        "mode": "login",
        "token": token,
        "user_id": user.id,
        "email": user.email,
        "role": user.role
    }
