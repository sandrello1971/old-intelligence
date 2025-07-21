from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.ticket import Ticket
from app.models.task import Task
from app.models.activity import Activity

ULISSE_ACTIVITY_TYPE_ID = 63705
DEFAULT_TASKS = ["Predisposizione incarico", "Invio incarico", "Firma incarico"]


def create_commessa_from_activity(activity_id: int, db: Session):
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Attività non trovata")

    if int(activity.sub_type_id) != ULISSE_ACTIVITY_TYPE_ID:
        raise HTTPException(status_code=400, detail="L'attività non è di tipo Ulisse (ID 63705)")

    suffix = str(activity.id)[-4:]
    ticket_code = f"TCK-I24-{suffix}-00"
    owner_id = activity.accompagnato_da

    existing_ticket = db.query(Ticket).filter(Ticket.ticket_code == ticket_code).first()
    if existing_ticket:
        raise HTTPException(status_code=400, detail="Ticket I24 già esistente")

    now = datetime.utcnow()
    ticket = Ticket(
        activity_id=activity.id,
        ticket_code=ticket_code,
        title="Incarico 24 mesi",
        gtd_type="Project",
        owner_id=owner_id,
        owner=activity.owner_name,
        account=activity.owner_name,
        status=0,
        priority=1,
        description=activity.description,
        customer_name=activity.customer_name,
        created_at=now,
        updated_at=now,
        detected_services=[],
        due_date=now + timedelta(days=3)
    )
    db.add(ticket)
    db.flush()

    for title in DEFAULT_TASKS:
        task = Task(
            ticket_id=ticket.id,
            title=title,
            status="aperto",
            priority=2,
            owner=str(owner_id),
            customer_name=ticket.customer_name,
            description=title,
            due_date=ticket.due_date
        )
        db.add(task)

    db.commit()

    return {
        "message": "Commessa I24 creata",
        "ticket_code": ticket.ticket_code,
        "activity_id": activity.id,
        "task_count": len(DEFAULT_TASKS)
    }
