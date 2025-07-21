from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel, validator
from openai import OpenAI
import os
import tempfile
import shutil
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from integrations.crm_incloud.sync import sync_single_activity
from app.services.crmsdk import create_crm_activity
from app.core.database import get_db
from app.services.crmsdk import get_company_id_by_name
from typing import Optional
from app.models import User

router = APIRouter(prefix="/ulisse/voice", tags=["ulisse"])

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo")


class TextInput(BaseModel):
    text: str


class ActivityInput(BaseModel):
    azienda: str
    servizi: list[str]
    priority: str = "bassa"
    transcript: Optional[str] = ""
    owner_email: Optional[str] = None

    @validator("priority")
    def validate_priority(cls, v):
        if v.lower() not in ["alta", "media", "bassa"]:
            raise ValueError('La priorita deve essere "alta", "media" o "bassa"')
        return v.lower()

    @validator("servizi")
    def validate_servizi(cls, v):
        if not v or len(v) == 0:
            raise ValueError("I servizi non possono essere vuoti.")
        return v


def map_priority(priority: str):
    return {"alta": 2, "media": 1, "bassa": 0}.get(priority, 0)


@router.post("/transcribe")
def transcribe_audio(audio: UploadFile = File(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            shutil.copyfileobj(audio.file, tmp)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as f:
            transcript = client.audio.transcriptions.create(model="whisper-1", file=f)
        os.remove(tmp_path)
        return {"text": transcript.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract")
def extract_entities(payload: TextInput):
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Estrai nome azienda e lista di servizi dal testo. Rispondi in JSON con 'azienda' e 'servizi'.",
                },
                {"role": "user", "content": payload.text},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content
        data = eval(content) if isinstance(content, str) else content

        if "azienda" not in data or "servizi" not in data:
            raise HTTPException(status_code=422, detail="Dati estratti non validi")
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create_activity")
def create_ulisse_activity(data: ActivityInput, db: Session = Depends(get_db)):
    try:
        company_id = get_company_id_by_name(data.azienda, db)
        if not company_id:
            raise HTTPException(status_code=404, detail="Azienda non trovata")

        user = db.query(User).filter(User.email == data.owner_email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Utente non trovato")

        activity_data = {
            "idCompanion": 120385,
            "subTypeId": 63705,
            "description": f"{data.transcript}\\n\\n---\\n\\n{', '.join(data.servizi)}",
            "ownerId": user.id,
            "companyId": company_id,
            "priority": map_priority(data.priority),
            "subject": f"Incarico 24 Mesi - {data.azienda}",
            "customer_name": data.azienda,
            "type": 7,
            "activityDate": datetime.utcnow().isoformat() + "Z",
            "activityEndDate": (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z",
        }

        response = create_crm_activity(activity_data)
        sync_single_activity(response, db)
        return {"id": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
