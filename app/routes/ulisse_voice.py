from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from pydantic import BaseModel, validator
from openai import OpenAI
import os
import tempfile
import shutil
import json
import mimetypes
import re
import subprocess
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from integrations.crm_incloud.sync import sync_single_activity
from app.services.crmsdk import create_crm_activity, get_company_id_by_name
from app.core.database import get_db
from typing import Optional
from app.models.owner import Owner
from app.auth.auth import get_current_user

router = APIRouter(prefix="/ulisse/voice", tags=["ulisse"])

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo")

class TextInput(BaseModel):
    text: str

class ActivityInput(BaseModel):
    azienda: str
    servizi: list[str]
    transcript: Optional[str] = ""

    @validator("servizi")
    def validate_servizi(cls, v):
        if not v or len(v) == 0:
            raise ValueError("I servizi non possono essere vuoti.")
        return v

def map_priority() -> int:
    return 0  # fisso: "bassa"

@router.post("/transcribe")
def transcribe_audio(audio: UploadFile = File(...)):
    try:
        content_type = audio.content_type or "application/octet-stream"
        extension = mimetypes.guess_extension(content_type) or ".webm"

        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp_in:
            shutil.copyfileobj(audio.file, tmp_in)
            input_path = tmp_in.name

        output_path = input_path.replace(extension, ".mp3")

        subprocess.run(
            ["ffmpeg", "-i", input_path, "-ar", "16000", output_path],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        with open(output_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )

        os.remove(input_path)
        os.remove(output_path)

        return {"text": transcript.text}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Errore trascrizione audio: {e}")

@router.post("/extract")
def extract_entities(payload: TextInput):
    print("Testo da analizzare:", payload.text)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Sei un assistente intelligente per l’estrazione di informazioni da testo parlato. "
                        "Riceverai un testo trascritto da voce umana.\n\n"
                        "Il tuo compito è:\n"
                        "- Estrarre il nome dell’azienda.\n"
                        "- Estrarre i servizi menzionati nel testo, correggendo eventuali errori ortografici o variazioni comuni.\n"
                        "- Rispondere **solo in JSON** con le chiavi: 'azienda' e 'servizi'.\n\n"
                        "La lista dei servizi consentiti è la seguente (e nessun altro):\n"
                        "- Finanziamenti\n"
                        "- Collaborazione\n"
                        "- Incarico 24 mesi\n"
                        "- Transizione 5.0\n"
                        "- Know How\n"
                        "- Bandi\n"
                        "- Altro\n"
                        "- Generico\n"
                        "- Patent Box\n"
                        "- Formazione 4.0\n"
                        "- Cashback\n\n"
                        "Se nel testo trovi varianti come 'patentbox', 'formazioni 4.0', 'formazione quattro punto zero', 'incentivi bandi europei' ecc., "
                        "prova a mappare al termine più vicino della lista sopra.\n"
                        "Se non riesci a mappare con certezza, lascia il servizio fuori.\n"
                        "Non inventare mai nuovi servizi.\n"
                        "Rispondi solo con JSON, senza testo extra."
                    )
                },
                {"role": "user", "content": payload.text}
            ],
            temperature=0.2
        )

        content = response.choices[0].message.content.strip()
        print("Risposta GPT:", content)

        if content.startswith("```"):
            content = re.sub(r"^```[a-z]*\n?", "", content, flags=re.IGNORECASE)
            content = content.rstrip("```").strip()

        try:
            data = json.loads(content) if isinstance(content, str) else content
        except Exception as parse_err:
            print("Errore parsing JSON:", parse_err)
            raise HTTPException(status_code=500, detail="Risposta GPT non è JSON valido")

        if not isinstance(data, dict) or not data.get("azienda") or not isinstance(data.get("servizi"), list) or not data["servizi"]:
            raise HTTPException(status_code=422, detail="Estrazione non valida: assicurati di menzionare azienda e almeno un servizio.")

        return data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore estrazione entità: {e}")

@router.post("/create_activity")
async def create_ulisse_activity(
    request: Request,
    db: Session = Depends(get_db),
    owner: Owner = Depends(get_current_user)
):
    try:
        body = await request.json()
        from pprint import pprint
        print("JSON raw ricevuto dal frontend:")
        pprint(body)

        data = ActivityInput(**body)

        print("Utente autenticato:")
        pprint(owner.__dict__)

        company_id = get_company_id_by_name(data.azienda, db)
        if not company_id:
            raise HTTPException(status_code=404, detail="Azienda non trovata")

        activity_data = {
            "idCompanion": 120385,
            "subTypeId": 63705,
            "description": f"{data.transcript}\n\n---\n\n{', '.join(data.servizi)}",
            "ownerId": owner.id,
            "companyId": company_id,
            "priority": 0,
            "subject": f"Incarico 24 Mesi - {data.azienda}",
            "customer_name": data.azienda,
            "type": 7,
            "activityDate": datetime.utcnow().isoformat() + "Z",
            "activityEndDate": (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z",
        }

        response = create_crm_activity(activity_data)
        sync_single_activity(response, db)
        return {"id": response, "success": True, "azienda": data.azienda, "servizi": data.servizi, "message": f"✅ Attività creata per {data.azienda} - Servizi: {", ".join(data.servizi)}"}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Errore creazione attività: {e}")

print("ulisse_voice router loaded")
