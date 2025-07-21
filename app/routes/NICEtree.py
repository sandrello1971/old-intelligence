# app/routes/tree.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.models.ticket import Ticket
from app.models.task import Task
from app.models.activity import Activity

router = APIRouter(prefix="/treeview", tags=["treeview"])

@router.get("/companies")
def get_company_tree(db: Session = Depends(get_db)):
    tickets = db.query(Ticket).options(
        joinedload(Ticket.tasks),
        joinedload(Ticket.activity)  # Include attività collegata
    ).all()

    companies = {}

    for ticket in tickets:
        customer_name = ticket.customer_name or "(Sconosciuto)"

        if customer_name not in companies:
            companies[customer_name] = {
                "name": customer_name,
                "commessa": None,
                "opportunities": []
            }

        # Prepara dati ticket completi
        ticket_data = {
            "id": ticket.id,
            "ticket_code": ticket.ticket_code,
            "customer_name": customer_name,
            "activity": {
                "id": ticket.activity.id if ticket.activity else None,
                "description": ticket.activity.description if ticket.activity else None,
            },
            "tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "status": t.status,
                    "priority": t.priority,
                } for t in ticket.tasks
            ]
        }

        # Incarico 24 mesi
        if ticket.ticket_code.startswith("TKC-M24"):
            if not companies[customer_name]["commessa"]:
                companies[customer_name]["commessa"] = {
                    "title": f"Commessa Incarico 24 mesi per {customer_name}",
                    "tickets": []
                }
            companies[customer_name]["commessa"]["tickets"].append(ticket_data)

        # Opportunità
        else:
            opportunity_type = extract_opportunity_code(ticket.ticket_code)
            found = False
            for opp in companies[customer_name]["opportunities"]:
                if opp["opportunity_code"] == opportunity_type:
                    opp["tickets"].append(ticket_data)
                    found = True
                    break
            if not found:
                companies[customer_name]["opportunities"].append({
                    "opportunity_code": opportunity_type,
                    "title": f"Opportunità {opportunity_type} - {customer_name}",
                    "tickets": [ticket_data]
                })

    return list(companies.values())

def extract_opportunity_code(ticket_code: str) -> str:
    if "-" in ticket_code:
        return ticket_code.split("-")[0]
    return "ALTRO"
