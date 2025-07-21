from datetime import datetime, timedelta
from collections import Counter
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.ticket import Ticket
from app.models.task import Task  # Import aggiunto

router = APIRouter(prefix="/statistics", tags=["statistics"])

# Codici ufficiali: codice → etichetta leggibile
SERVICE_LABELS = {
    "FNZ": "Finanziamenti",
    "COL": "Collaborazione",
    "M24": "Incarico 24 mesi",
    "T50": "Transizione 5.0",
    "KHW": "Know How",
    "BND": "Bandi",
    "ZZZ": "Altro",
    "AAA": "Generico",
    "PBX": "Patent Box",
    "F40": "Formazione 4.0",
    "CBK": "Cashback",
}
VALID_SERVICES = set(SERVICE_LABELS.keys())

# Mappa da nomi comuni → codici
SERVICE_MAPPING = {
    "formazione 4.0": "F40",
    "patent box": "PBX",
    "transizione 5.0": "T50",
    "incarico 24 mesi": "M24",
    "bandi": "BND",
    "cashback": "CBK",
    "finanziamenti": "FNZ",
    "collaborazione": "COL",
    "know how": "KHW",
    "generico": "AAA",
    "altro": "ZZZ"
}

@router.get("/global")
def global_statistics(db: Session = Depends(get_db)):
    # -------- TICKET STATS --------
    tickets = db.query(Ticket).all()
    today = datetime.utcnow().date()
    green_threshold = today + timedelta(days=3)

    by_status = Counter()
    by_priority = Counter()
    by_owner = Counter()
    service_counter = Counter()
    semafori = {"green": 0, "yellow": 0, "red": 0}

    for t in tickets:
        by_status[t.status or 0] += 1
        by_priority[t.priority or 0] += 1
        by_owner[t.owner or "Sconosciuto"] += 1

        if t.due_date:
            due = t.due_date.date()
            if due < today:
                semafori["red"] += 1
            elif due <= green_threshold:
                semafori["yellow"] += 1
            else:
                semafori["green"] += 1
        else:
            semafori["red"] += 1

        if t.detected_services:
            for service in t.detected_services:
                key = service.strip().lower()
                code = SERVICE_MAPPING.get(key)
                if code in VALID_SERVICES:
                    service_counter[code] += 1
                else:
                    service_counter["ZZZ"] += 1
        else:
            service_counter["ZZZ"] += 1

    tickets_stats = {
        "total": len(tickets),
        "by_status": dict(by_status),
        "by_priority": dict(by_priority),
        "semafori": semafori,
        "by_owner": dict(by_owner),
        "gtd_type_data": {
            "labels": [SERVICE_LABELS.get(code, code) for code in service_counter.keys()],
            "values": list(service_counter.values())
        }
    }

    # -------- TASK STATS --------
    tasks = db.query(Task).all()
    task_by_status = Counter()
    task_by_priority = Counter()
    task_by_owner = Counter()

    for task in tasks:
        task_by_status[task.status or "sconosciuto"] += 1
        task_by_priority[task.priority or "sconosciuto"] += 1
        task_by_owner[task.owner or "Sconosciuto"] += 1

    tasks_stats = {
        "total": len(tasks),
        "by_status": dict(task_by_status),
        "by_priority": dict(task_by_priority),
        "by_owner": dict(task_by_owner)
    }

    return {
        "tickets_stats": tickets_stats,
        "tasks_stats": tasks_stats
    }
