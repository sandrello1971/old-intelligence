from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Union
from sqlalchemy.orm import Session
import json
import os
import openai
from datetime import datetime

from app.core.database import get_db
from app.models.assessment_session import AssessmentSession

# Configurazione
openai.api_key = os.getenv("OPENAI_API_KEY")

router = APIRouter()

# ======== MODELLI DATI ========
class AziendaInfo(BaseModel):
    nome: str
    settore: str
    dimensione: str
    referente: str
    email: str

class RisposteUtente(BaseModel):
    azienda: AziendaInfo
    risposte: Dict[str, Union[List[str], int]]

# ======== CARICAMENTO DATI STATICI ========
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

with open(os.path.join(STATIC_DIR, "digital_maturity_questions.json"), "r", encoding="utf-8") as f:
    QUESTIONARIO = json.load(f)

with open(os.path.join(STATIC_DIR, "benchmark.json"), "r", encoding="utf-8") as f:
    BENCHMARK = json.load(f)

# ======== ENDPOINT ========
@router.get("/api/questions")
def get_questions():
    return JSONResponse(content=QUESTIONARIO)

@router.post("/api/analyze")
def analyze_submission(data: RisposteUtente, db: Session = Depends(get_db)):
    punteggi = {}
    for qid, risposta in data.risposte.items():
        sezione = qid.split("_")[0]
        score = len(risposta) if isinstance(risposta, list) else risposta
        punteggi.setdefault(sezione, []).append(score)

    risultati = {k: round(sum(v) / len(v), 2) for k, v in punteggi.items()}

    # Gap rispetto al benchmark
    gap = {}
    for k, v in risultati.items():
        benchmark = BENCHMARK.get(k, 3.0)
        gap[k] = round(benchmark - v, 2)

    # Salvataggio sessione (senza raccomandazioni per ora)
    session = AssessmentSession(
        company_id=None,
        azienda_nome=data.azienda.nome,
        settore=data.azienda.settore,
        dimensione=data.azienda.dimensione,
        referente=data.azienda.referente,
        email=data.azienda.email,
        risposte_json=data.risposte,
        punteggi_json=risultati,
        raccomandazioni="",
        creato_il=datetime.utcnow()
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {"punteggi": risultati, "gap": gap, "session_id": str(session.id)}

@router.post("/api/recommendations")
def generate_recommendations(data: RisposteUtente, db: Session = Depends(get_db)):
    analyze_result = analyze_submission(data, db)
    risultati, gap, session_id = analyze_result["punteggi"], analyze_result["gap"], analyze_result["session_id"]
    debolezze = [k for k, v in gap.items() if v > 1.0]

    prompt = f"""
    Azienda:
    - Nome: {data.azienda.nome}
    - Settore: {data.azienda.settore}
    - Dimensione: {data.azienda.dimensione}

    Aree con carenza di maturità digitale:
    - {', '.join(debolezze)}

    Servizi disponibili:
    - RPA
    - CRM AI
    - Formazione digitale
    - Data Integration

    Suggerisci una strategia per colmare i gap, usando servizi basati su AI.
    """

    completions = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Sei un consulente esperto in trasformazione digitale."},
            {"role": "user", "content": prompt}
        ]
    )

    response = completions.choices[0].message.content

    # Aggiorna raccomandazioni nella sessione salvata
    session = db.query(AssessmentSession).filter_by(id=session_id).first()
    if session:
        session.raccomandazioni = response
        db.commit()

    return {"raccomandazioni": response}
