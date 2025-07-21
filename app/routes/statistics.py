from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.ticket import Ticket
from app.models.task import Task
from app.models.opportunity import Opportunity

router = APIRouter(prefix="/api/statistics", tags=["statistics"])

STATUS_MAP = {
    0: "aperto",
    1: "in_corso",
    2: "chiuso",
    "aperto": "aperto",
    "in_corso": "in_corso",
    "chiuso": "chiuso"
}

@router.get("/i24/count")
def count_i24_tickets(db: Session = Depends(get_db)):
    return db.query(Ticket).filter(Ticket.ticket_code.like("TCK-I24-%")).count()

@router.get("/i24/status")
def i24_status(db: Session = Depends(get_db)):
    tickets = db.query(Ticket).filter(Ticket.ticket_code.like("TCK-I24-%")).all()
    ticket_statuses = {"aperto": 0, "in_corso": 0, "chiuso": 0}
    task_statuses = {"aperto": 0, "in_corso": 0, "chiuso": 0}
    
    for t in tickets:
        ticket_state = STATUS_MAP.get(t.status)
        if ticket_state:
            ticket_statuses[ticket_state] += 1
        for task in t.tasks:
            task_state = STATUS_MAP.get(task.status)
            if task_state:
                task_statuses[task_state] += 1

    return {
        "ticket_statuses": ticket_statuses,
        "task_statuses": task_statuses
    }

@router.get("/opportunity/phases")
def opportunity_phases(db: Session = Depends(get_db)):
    results = {}
    opportunities = db.query(Opportunity).all()
    for opp in opportunities:
        for phase in opp.phases:
            label = phase.name
            if label not in results:
                results[label] = {"aperto": 0, "in_corso": 0, "chiuso": 0}
            status_key = STATUS_MAP.get(phase.status)
            if status_key:
                results[label][status_key] += 1
    return results

@router.get("/opportunity/by_type")
def opportunity_by_type(db: Session = Depends(get_db)):
    from app.models.activity import Activity  # Import locale per evitare cicli
    from app.models.ticket import Ticket
    from app.models.task import Task

    STATUS_MAP = {
        0: "aperto",
        1: "in_corso",
        2: "chiuso",
        "aperto": "aperto",
        "in_corso": "in_corso",
        "chiuso": "chiuso"
    }

    opportunities = db.query(Opportunity).all()
    data = {}

    for opp in opportunities:
        code = opp.codice or "unknown"
        type_code = code.split("-")[0] if "-" in code else code

        if type_code not in data:
            data[type_code] = {
                "totali": 0,
                "fasi": {}
            }

        data[type_code]["totali"] += 1

        # Trova attività collegate
        activities = db.query(Activity).filter(Activity.opportunity_id == str(opp.id)).all()

        for act in activities:
            tickets = db.query(Ticket).filter(Ticket.activity_id == act.id).all()
            for ticket in tickets:
                tasks = db.query(Task).filter(Task.ticket_id == ticket.id).all()
                for task in tasks:
                    fase = task.title or "Senza titolo"
                    stato = STATUS_MAP.get(task.status, "unknown")

                    if fase not in data[type_code]["fasi"]:
                        data[type_code]["fasi"][fase] = {"aperto": 0, "in_corso": 0, "chiuso": 0}

                    if stato in data[type_code]["fasi"][fase]:
                        data[type_code]["fasi"][fase][stato] += 1

    return data
