# app/routes/projects.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.models.ticket import Ticket
from app.models.task import Task

router = APIRouter(tags=["projects"])

@router.get("/projects/tree")
def get_project_tree(db: Session = Depends(get_db)):
    tickets = db.query(Ticket).options(joinedload(Ticket.tasks)).all()

    # Raggruppiamo i dati per azienda (customer_name)
    projects = {}
    for ticket in tickets:
        customer_name = ticket.customer_name or "Sconosciuto"
        if customer_name not in projects:
            projects[customer_name] = {
                "customer_name": customer_name,
                "commessa": "Incarico 24 mesi",  # fissa per ora
                "tickets": [],
                "opportunities": []  # riempiremo dopo
            }

        projects[customer_name]["tickets"].append({
            "ticket_id": ticket.id,
            "ticket_code": ticket.ticket_code,
            "title": ticket.title,
            "tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status,
                    "priority": task.priority,
                }
                for task in ticket.tasks
            ]
        })

    return list(projects.values())

# Poi in app/main.py --> include_router(router)!
