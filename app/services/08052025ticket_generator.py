import os
import json
import re
from datetime import datetime, timedelta
from openai import OpenAI
from sqlalchemy.orm import Session
from app.models.ticket import Ticket
from app.models.task import Task
from app.models.activity import Activity
from process_code_map import PROCESS_CODE_MAP
from process_templates import PROCESS_TEMPLATES
from integrations.crm_incloud.activity import create_crm_activity

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo")
STATUS_MAP = {"aperta": 0, "in corso": 1, "completata": 2}
PRIORITY_CRM = {1: "High", 2: "Medium", 3: "Low"}

SERVICE_LABELS = {
    "F40": "Formazione 4.0",
    "KHW": "Know How",
    "T50": "Transizione 5.0",
    "PBX": "Patent Box",
    "CBK": "Cashback",
    "FND": "Finanziamenti",
    "BND": "Bandi",
    "CLB": "Collaborazione",
    "GEN": "Generico",
    "ALT": "Altro",
}

def gtd_priority_to_int(priority: str) -> int:
    mapping = {
        "alta": 1,
        "media": 2,
        "bassa": 3
    }
    return mapping.get(priority.lower().strip(), 2) if isinstance(priority, str) else 2

def extract_json_block(text: str) -> str:
    match = re.search(r'\[\s*{.*?}\s*]', text, re.DOTALL)
    if match:
        return match.group(0)
    raise ValueError("⚠️ Nessun blocco JSON valido trovato nella risposta GPT.")

def extract_project_codes_local(description: str) -> list[str]:
    description_lower = description.lower()
    matches = []
    for key, code in PROCESS_CODE_MAP.items():
        pattern = r'\b' + re.escape(key.lower()) + r'\b'
        if re.search(pattern, description_lower):
            matches.append(code)
    print(f"[DEBUG] Progetti rilevati nella descrizione: {matches}")
    return matches

def update_activity_description_from_tasks(activity: Activity, db: Session):
    all_tasks = db.query(Task).filter(Task.ticket.has(activity_id=activity.id)).all()
    titles = [f"{t.title}: {t.description}" for t in all_tasks]
    activity.description = " | ".join(titles)
    db.merge(activity)
    db.commit()

def update_activity_owner(activity: Activity, new_owner_id: int, db: Session):
    if str(activity.accompagnato_da) != str(new_owner_id):
        activity.accompagnato_da = str(new_owner_id)
        db.merge(activity)
        db.commit()
        print(f"[INFO] Owner aggiornato per attività #{activity.id} → {new_owner_id}")

def generate_tickets_from_activity(activity: Activity, db: Session, sync_mode: bool = False):
    print(f"\n[INFO] Generazione ticket per attività #{activity.id}")
    print(f"[INFO] Descrizione attività: {activity.description}")

    suffix = str(activity.id)[-4:]
    owner_id = activity.accompagnato_da

    # Se l'attività è di tipo "Incarico 24 mesi" (I24), crea solo ticket e task
    if int(activity.sub_type_id) == 63705:  # Incarico 24 mesi (Ulisse)
        print("[INFO] Attività di tipo 'Incarico 24 mesi' trovata. Creazione ticket e task direttamente.")

        # Creazione ticket per l'attività I24 (Incarico 24 mesi)
        now = datetime.utcnow()
        parent_code = f"TCK-I24-{suffix}-00"
        parent_ticket = Ticket(
            activity_id=activity.id,
            ticket_code=parent_code,
            title="Incarico 24 mesi",
            gtd_type="Project",
            owner_id=owner_id,
            owner=activity.owner_name,
            status=0,  # "aperto"
            priority=1,
            description=activity.description,
            customer_name=activity.customer_name,
            created_at=now,
            updated_at=now,
        )
        db.add(parent_ticket)
        db.flush()

        parent_ticket.due_date = now + timedelta(days=3)
        db.add(parent_ticket)

        # Crea i task fittizi per "Incarico 24 mesi"
        for task_title in ["Predisposizione incarico", "Invio incarico", "Firma incarico"]:
            task = Task(
                ticket_id=parent_ticket.id,
                title=task_title,
                status="aperto",
                priority="media",
                owner=str(activity.owner_id),
                customer_name=parent_ticket.customer_name,
                description=task_title,
                parent_id=None
            )
            db.add(task)

        db.commit()
        print(f"[SUCCESS] Ticket e task creati per attività Incarico 24 mesi con codice: {parent_ticket.ticket_code}")

        return [parent_ticket]  # Restituiamo il ticket appena creato

    # Se non è "Incarico 24 Mesi", continua con la logica delle milestone (che non serve qui)
    print("[INFO] Attività non di tipo 'Incarico 24 Mesi', procedo con altre logiche.")
    # Logica per altre attività (futuro)
    # ...

    db.commit()
    return []  # In caso non ci siano ticket creati

__all__ = ["generate_tickets_from_activity", "update_activity_owner"]
