# app/routes/tree.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.models.ticket import Ticket
from app.models.task import Task
from app.models.activity import Activity
from app.models.opportunity import Opportunity

router = APIRouter(prefix="/treeview", tags=["treeview"])

@router.get("/companies")
def get_company_tree(db: Session = Depends(get_db)):
    tickets = db.query(Ticket).options(
        joinedload(Ticket.tasks),
        joinedload(Ticket.activity),
        joinedload(Ticket.company),  # 👈 AGGIUNTO
    ).all()

    companies = {}

    for ticket in tickets:
        customer_name = (
            ticket.customer_name or
            (ticket.company.nome if ticket.company else None) or
            "(Sconosciuto)"
        )

        if customer_name not in companies:
            companies[customer_name] = {
                "name": customer_name,
                "commessa": None,
                "opportunities": []
            }

            crm_opps = db.query(Opportunity).filter(Opportunity.cliente == customer_name).all()
            for opp in crm_opps:
                has_activities = db.query(Activity).filter(Activity.opportunity_id == str(opp.id)).count() > 0
                companies[customer_name]["opportunities"].append({
                    "opportunity_code": opp.codice,
                    "title": opp.titolo,
                    "id": opp.id,
                    "has_activities": has_activities,
                    "tickets": []
                })

        ticket_data = {
            "id": ticket.id,
            "ticket_code": ticket.ticket_code,
            "title": f"{ticket.ticket_code} - {ticket.title}",
            "customer_name": customer_name,
            "gtd_generated": ticket.gtd_generated,
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
       if ticket.ticket_code.startswith("TCK-I24") or (
           ticket.activity and str(ticket.activity.opportunity_id) in ("", "0", None)
       ):
           if not companies[customer_name]["commessa"]:
               companies[customer_name]["commessa"] = {
                   "title": f"Commessa Incarico 24 mesi per {customer_name}",
                   "tickets": []
               }
           companies[customer_name]["commessa"]["tickets"].append(ticket_data)
        else:
            opportunity_type = extract_opportunity_code(ticket.ticket_code)
            found = False
            for opp in companies[customer_name]["opportunities"]:
                if opp["opportunity_code"].startswith(opportunity_type):
                    opp["tickets"].append(ticket_data)
                    found = True
                    break
            if not found:
                companies[customer_name]["opportunities"].append({
                    "opportunity_code": opportunity_type,
                    "title": f"Opportunità {opportunity_type} - {customer_name}",
                    "id": None,
                    "has_activities": False,
                    "tickets": [ticket_data]
                })

    return list(companies.values())



def extract_opportunity_code(ticket_code: str) -> str:
    parts = ticket_code.replace("TCK-", "").split("-")
    return parts[0] if parts else "ALTRO"
