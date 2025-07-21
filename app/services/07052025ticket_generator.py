import os
import json
import re
from datetime import datetime, timedelta
from openai import OpenAI
from sqlalchemy.orm import Session
from app.models.ticket import Ticket
from app.models.task import Task
from app.models.activity import Activity
from app.models.milestone import Milestone  # 🔄 Per ordine milestone
from process_code_map import PROCESS_CODE_MAP
from process_templates import PROCESS_TEMPLATES

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo")
STATUS_MAP = {"aperta": 0, "in corso": 1, "completata": 2}

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
    return mapping.get(priority.lower().strip(), 2)

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

def generate_tickets_from_activity(activity: Activity, db: Session):
    print(f"\n[INFO] Generazione ticket per attività #{activity.id}")
    print(f"[INFO] Descrizione attività: {activity.description}")

    suffix = str(activity.id)[-4:]
    owner_id = activity.accompagnato_da

    if db.query(Activity).filter_by(id=activity.id).first():
        print("[INFO] Attività già presente. Skip insert.")
    else:
        activity.sub_type_id = 63705
        activity.accompagnato_da = owner_id
        db.add(activity)

    project_codes = extract_project_codes_local(activity.description)
    project_labels = [SERVICE_LABELS.get(code, code) for code in project_codes]

    if int(activity.sub_type_id) == 63705:
        print("[DEBUG] Attività Ulisse rilevata, creazione ticket unico.")

        now = datetime.utcnow()
        parent_code = f"TCK-I24-{suffix}-00"

        parent_ticket = Ticket(
            activity_id=activity.id,
            ticket_code=parent_code,
            title=f"Incarico 24 mesi - {parent_code}",
            gtd_type="Project",
            owner_id=owner_id,
            owner=activity.owner_name,
            account=activity.owner_name,
            status=STATUS_MAP.get(activity.status, 0),
            priority=1,
            description=activity.description,
            customer_name=activity.customer_name,
            created_at=now,
            updated_at=now,
            detected_services=project_labels
        )
        db.add(parent_ticket)
        db.flush()

        parent_ticket.due_date = now + timedelta(days=3)
        db.add(parent_ticket)

        default_tasks = ["Predisposizione incarico", "Invio incarico", "Firma incarico"]
        for task_title in default_tasks:
            task = Task(
                ticket_id=parent_ticket.id,
                title=task_title,
                status="aperto",
                priority=2,
                owner=str(activity.owner_id),
                customer_name=parent_ticket.customer_name,
                description=task_title,
                due_date=parent_ticket.due_date,
                parent_id=None
            )
            db.add(task)

        db.commit()
        print(f"[SUCCESS] Ticket Ulisse creato: {parent_ticket.ticket_code}")
        return [parent_ticket]

    all_tickets = []

    if not project_codes:
        print("[WARN] Nessun codice progetto rilevato.")
        return []

    milestones = db.query(Milestone).filter(Milestone.project_type.in_(project_codes)).all()
    ordered_codes = [m.project_type for m in sorted(milestones, key=lambda m: m.order)]

    for process_code in ordered_codes:
        print(f"[DEBUG] Elaborazione progetto {process_code}")

        template_tasks = PROCESS_TEMPLATES.get(process_code, [])
        if not template_tasks:
            print(f"[WARN] Nessun template per il processo {process_code}, skip.")
            continue

        parent_code = f"TCK-{process_code}-{suffix}-00"
        print(f"[INFO] Creazione ticket padre: {parent_code}")

        parent_ticket = Ticket(
            activity_id=activity.id,
            ticket_code=parent_code,
            title=f"{template_tasks[0]} - {parent_code}",
            gtd_type="Project",
            owner_id=owner_id,
            owner=activity.owner_name,
            status=STATUS_MAP.get(activity.status, 0),
            priority=1,
            description=activity.description,
            customer_name=activity.customer_name,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            detected_services=[SERVICE_LABELS.get(process_code, process_code)]
        )
        db.add(parent_ticket)
        db.flush()

        for task_title in template_tasks:
            task = Task(
                ticket_id=parent_ticket.id,
                title=task_title,
                status="aperto",
                priority=2,
                owner=str(activity.owner_id),
                customer_name=parent_ticket.customer_name,
                description=task_title,
                parent_id=None
            )
            db.add(task)

        all_tickets.append(parent_ticket)

    db.commit()
    print(f"[SUCCESS] Ticket creati: {[t.ticket_code for t in all_tickets]}")
    return all_tickets

__all__ = ["generate_tickets_from_activity"]
