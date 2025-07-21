# app/routes/tasks.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.models.task import Task
from app.models.ticket import Ticket
from app.models.owner import Owner
from app.services.crm_parser import extract_opportunities_from_description
from app.services.opportunity_creator import create_and_sync_opportunities
from app.utils.service_detection import extract_services_from_description
from app.models.user import User

router = APIRouter(tags=["tasks"])

task = db.query(Task).filter(Task.id == task_id).first()

owner = db.query(User).filter(User.id == int(task.owner)).first() if task.owner else None

@router.get("/tasks/{task_id}")
def get_task_detail(task_id: int, db: Session = Depends(get_db)):
    task = (
        db.query(Task)
        .options(
            joinedload(Task.owner_ref),
            joinedload(Task.predecessor_ref),
            joinedload(Task.ticket).joinedload(Ticket.tasks)
        )
        .filter(Task.id == task_id)
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="Task non trovato")

    return {
        "id": task.id,
        "ticket_id": task.ticket_id,
        "ticket_code": task.ticket.ticket_code if task.ticket else None,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "owner": task.owner,
        "owner_name": f"{task.owner_ref.name} {task.owner_ref.surname}" if task.owner_ref else None,
        "predecessor_id": task.predecessor_id,
        "predecessor_title": task.predecessor_ref.title if task.predecessor_ref else None,
        "siblings": [
            {"id": t.id, "title": t.title}
            for t in (task.ticket.tasks if task.ticket else [])
            if t.id != task.id
        ]
    }

@router.patch("/tasks/{task_id}")
def update_task(task_id: int, payload: dict, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task non trovato")

    for field in ["description", "status", "priority", "predecessor_id", "owner"]:
        if field in payload:
            value = payload[field]
            if field == "predecessor_id" and value == "":
                value = None
            setattr(task, field, value)

    db.commit()
    db.refresh(task)

    # 🔥 Se chiuso, estrai opportunità da creare
    if task.status == "chiuso":
        ticket = db.query(Ticket).filter(Ticket.id == task.ticket_id).first()
        if ticket:
            opportunities = extract_opportunities_from_description(ticket.description)
            if opportunities:
                return {"pending_opportunities": opportunities}

    # Altrimenti ritorna task aggiornato
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "ticket_id": task.ticket_id,
        "ticket_code": task.ticket.ticket_code if task.ticket else None,
        "owner": task.owner,
        "owner_name": f"{task.owner_ref.name} {task.owner_ref.surname}" if task.owner_ref else None
    }

@router.post("/tasks/{task_id}/confirm-create-opportunities")
def confirm_create_opportunities(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task non trovato")

    ticket = db.query(Ticket).filter(Ticket.id == task.ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trovato")

    if not ticket.activity:
        raise HTTPException(status_code=404, detail="Attività non collegata al ticket")

    # ✅ Estrai i servizi dalla descrizione dell'attività
    from app.utils.service_detection import extract_services_from_description
    services = extract_services_from_description(ticket.activity.description or "")
    
    # ✅ Salva i servizi rilevati nell'attività
    ticket.activity.detected_services = ", ".join(services)
    db.commit()

    # 🧪 Simulazione creazione opportunità/attività (può essere estesa)
    return {
        "message": "Servizi rilevati e salvati",
        "detected_services": services,
        "activity_id": ticket.activity.id,
        "ticket_code": ticket.ticket_code
    }

@router.get("/tasks")
def list_tasks(ticket_id: int = Query(None), db: Session = Depends(get_db)):
    if ticket_id:
        tasks = db.query(Task).filter(Task.ticket_id == ticket_id).all()
    else:
        tasks = db.query(Task).all()

    return [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "status": t.status,
            "priority": t.priority,
            "ticket_id": t.ticket_id,
            "owner": t.owner,
            "predecessor_id": t.predecessor_id,
            "milestone_id": t.milestone_id
        }
        for t in tasks
    ]
