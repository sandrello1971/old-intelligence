import os
import json
import re
from openai import OpenAI
from sqlalchemy.orm import Session
from app.models.ticket import Ticket
from app.models.task import Task
from app.models.activity import Activity
from process_code_map import PROCESS_CODE_MAP
from process_templates import PROCESS_TEMPLATES

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo")

def gtd_priority_to_int(priority: str) -> int:
    mapping = {
        "alta": 1,
        "media": 2,
        "bassa": 3
    }
    return mapping.get(priority.lower().strip(), 2)

def extract_json_block(text: str) -> str:
    match = re.search(r'\[\s*{.*?}\s*]', text, re.DOTALL)
    if match:
        return match.group(0)
    raise ValueError("⚠️ Nessun blocco JSON valido trovato nella risposta GPT.")

def extract_project_codes_local(description: str) -> list[str]:
    """
    Estrae tutti i codici progetto (F40, T50, ecc.) dalla descrizione dell'attività
    basandosi sulle chiavi in PROCESS_CODE_MAP.
    """
    description_lower = description.lower()
    matches = []

    for key, code in PROCESS_CODE_MAP.items():
        pattern = r'\b' + re.escape(key.lower()) + r'\b'
        if re.search(pattern, description_lower):
            matches.append(code)

    print(f"[DEBUG] Progetti rilevati nella descrizione: {matches}")
    return matches

def generate_tickets_from_activity(activity: Activity, db: Session):
    """
    Genera un ticket padre per ogni progetto rilevato nella descrizione dell'attività,
    ciascuno con una lista di task figli associati.
    """
    print(f"\n[INFO] Generazione ticket per attività #{activity.id}")
    print(f"[INFO] Descrizione attività: {activity.description}")

    process_codes = extract_project_codes_local(activity.description)
    all_tickets = []

    if not process_codes:
        print("[WARN] Nessun codice progetto rilevato.")
        return []

    suffix = str(activity.id)[-4:]
    owner_id = activity.accompagnato_da

    for process_code in process_codes:
        print(f"[DEBUG] Elaborazione progetto {process_code}")

        template_tasks = PROCESS_TEMPLATES.get(process_code, [])
        if not template_tasks:
            print(f"[WARN] Nessun template per il processo {process_code}, skip.")
            continue

        parent_code = f"TKC-{process_code}-{suffix}-00"
        print(f"[INFO] Creazione ticket padre: {parent_code}")

        parent_ticket = Ticket(
            activity_id=activity.id,
            ticket_code=parent_code,
            title=f"Progetto {process_code}",
            gtd_type="Project",
            owner_id=owner_id,
            priority=1
        )
        db.add(parent_ticket)
        db.flush()

        for i, title in enumerate(template_tasks, start=1):
            task = Task(
                ticket_id=parent_ticket.id,
                title=title,
                priority=2
            )
            db.add(task)

        all_tickets.append(parent_ticket)

    db.commit()

    print(f"[SUCCESS] Ticket creati: {[t.ticket_code for t in all_tickets]}")
    return all_tickets
