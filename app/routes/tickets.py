from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import List
from app.core.database import get_db
from app.models import Ticket, Activity, Task, PhaseTemplate
from app.schemas.opportunity import OpportunityCreate
from integrations.crm_incloud.opportunity import create_crm_opportunity
from integrations.crm_incloud.generation import generate_opportunities_from_ticket
from app.models.user import User
from fastapi import Query
from datetime import date
from pydantic import BaseModel

router = APIRouter(tags=["tickets"])

def map_priority(priority: str):
    return {"alta": 2, "media": 1, "bassa": 0}.get(priority)

class ServiziInput(BaseModel):
    services: List[str]

@router.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = (
        db.query(Ticket)
        .options(
            joinedload(Ticket.tasks),
            joinedload(Ticket.activity)  # Assicurati che venga caricata anche l'attività
        )
        .filter(Ticket.id == ticket_id)
        .first()
    )

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trovato")
    account_name = (
        ticket.activity.owner_name if ticket.activity and ticket.activity.owner_name else None
    )

    enriched_tasks = []
    for t in (ticket.tasks or []):
        owner = db.query(User).filter(User.id == t.owner).first()
        owner_name = f"{owner.name} {owner.surname}" if owner else None
        enriched_tasks.append({
            "id": t.id,
            "title": t.title,
            "status": t.status,
            "priority": t.priority,
            "owner": t.owner,
            "owner_name": owner_name,
            "customer_name": ticket.customer_name,
            "due_date": t.due_date
        })

    # Usa i servizi dall'attività invece del ticket
    detected_services = ticket.activity.detected_services if ticket.activity else []

    return {
        "id": ticket.id,
        "ticket_code": ticket.ticket_code,
        "title": ticket.title,
        "description": ticket.description,
        "priority": ticket.priority,
        "status": ticket.status,
        "due_date": ticket.due_date,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
        "owner_id": ticket.owner_id,
        "gtd_type": ticket.gtd_type,
        "assigned_to": ticket.assigned_to,
        "owner": ticket.owner,
        "account": ticket.account,
        "milestone_id": ticket.milestone_id,
        "customer_name": ticket.customer_name,
            "due_date": t.due_date,
        "gtd_generated": ticket.gtd_generated,
        "detected_services": detected_services,  # Usa i servizi dell'attività
        "activity": {
            "id": ticket.activity.id if ticket.activity else None,
            "description": ticket.activity.description if ticket.activity else None,
            "detected_services": detected_services
        },
        "tasks": enriched_tasks
    }


from fastapi import Query  # già discusso

@router.get("/tickets")
def list_tickets(
    priority: str = Query(None),
    status: str = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Ticket)

    if priority:
        priority_value = map_priority(priority.lower())
        if priority_value is None:
            raise HTTPException(status_code=400, detail="Valore 'priority' non valido")
        query = query.filter(Ticket.priority == priority_value)

    if status:
        query = query.filter(Ticket.status == status)

    tickets = query.order_by(Ticket.created_at.desc(), Ticket.id.desc()).all()
    return [
        {
            "id": t.id,
            "ticket_code": t.ticket_code,
            "title": t.title,
            "description": t.description,
            "priority": t.priority,
            "status": t.status,
            "due_date": t.due_date,
            "created_at": t.created_at,
            "updated_at": t.updated_at,
            "owner_id": t.owner_id,
            "gtd_type": t.gtd_type,
            "assigned_to": t.assigned_to,
            "owner": t.owner,
            "milestone_id": t.milestone_id,
            "customer_name": t.customer_name,
            "gtd_generated": t.gtd_generated,
        }
        for t in tickets
    ]	

@router.post("/tickets/{ticket_id}/generate-all")
def generate_all(ticket_id: int, payload: ServiziInput, db: Session = Depends(get_db)):
    servizi = payload.services
    print("SERVIZI RICEVUTI:", servizi)
    result = generate_opportunities_from_ticket(ticket_id, servizi, db)
    return {"success": True, "details": result}

@router.post("/tickets/{ticket_id}/auto_generate_from_services")
def auto_generate_from_services(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter_by(id=ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trovato")

    if not ticket.detected_services:
        raise HTTPException(status_code=400, detail="Nessun servizio rilevato nel ticket")

    try:
        services = ticket.detected_services.split(",")  # oppure json.loads() se è JSON
        results = []

        for service in services:
            service = service.strip()
            activity_id_suffix = str(ticket.activity.id)[-4:]
            new_ticket_code = f"TCK-{service[:3].upper()}-{ticket.id}-01"
            new_ticket = Ticket(
                title=f"Auto da {service}",
                ticket_code=new_ticket_code,
                priority=ticket.priority,
                status="aperto",
                customer_name=ticket.customer_name,
                gtd_type="Project",
                owner_id=ticket.owner_id
            )
            db.add(new_ticket)
            db.flush()

            task = Task(
                title=f"Fase iniziale: {service}",
                ticket_id=new_ticket.id,
                priority=2,
                status="aperto"
            )
            db.add(task)
            results.append(new_ticket.ticket_code)

        db.commit()
        return {"status": "ok", "created": results}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tickets/{ticket_id}/generate_crm_opportunities")
def generate_crm_opportunities_from_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trovato")
    
    if not ticket.ticket_code.startswith("TCK-I24"):
        raise HTTPException(status_code=400, detail="Ticket non valido per generazione opportunità")

    tasks = db.query(Task).filter(Task.ticket_id == ticket_id).all()
    if not all(t.status == "chiuso" for t in tasks):
        raise HTTPException(status_code=400, detail="Tutti i task devono essere chiusi")

    from app.services.opportunity_creator import create_and_sync_opportunities
    result = create_and_sync_opportunities(ticket, db_session=db)
    return {"status": "ok", "opportunities_created": result}


@router.post("/tickets/auto_close_completed")
def auto_close_completed_tickets(db: Session = Depends(get_db)):
    tickets = db.query(Ticket).all()
    updated = 0
    closed_ids = []

    for ticket in tickets:
        tasks = db.query(Task).filter(Task.ticket_id == ticket.id).all()
        if tasks and all(t.status == "chiuso" for t in tasks) and ticket.status != 2:
            ticket.status = 2  # 2 = chiuso
            closed_ids.append(ticket.id)
            updated += 1

    db.commit()

    return {
        "tickets_chiusi": updated,
        "ids": closed_ids
    }
