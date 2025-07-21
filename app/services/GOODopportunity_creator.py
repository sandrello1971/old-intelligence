# app/services/opportunity_creator.py

from datetime import datetime
from app.services.crm_parser import extract_opportunities_from_description
from integrations.crm_incloud.opportunity import create_crm_opportunity
from app.models.ticket import Ticket
from app.models.task import Task
from app.models.company import Company
from app.core.database import SessionLocal


def create_and_sync_opportunities(ticket: Ticket, db_session=None):
    if db_session is None:
        db_session = SessionLocal()

    if not ticket.customer_name:
        raise Exception(f"Ticket ID {ticket.id} - Manca il nome dell'azienda (customer_name).")

    if not ticket.owner:
        raise Exception(f"Ticket ID {ticket.id} - Manca il nome dell'owner.")

    company = db_session.query(Company).filter(Company.nome == ticket.customer_name.strip()).first()
    if not company:
        raise Exception(f"Azienda '{ticket.customer_name}' non trovata nella tabella companies. Impossibile ottenere il crossId.")

    description = ticket.description or ""
    opportunities = extract_opportunities_from_description(description)
    created = []

    for opp_code in opportunities:
        payload = {
            "title": f"[{opp_code}] - {ticket.customer_name}",
            "crossId": company.id,
            "ownerId": int(ticket.owner_id),
            "description": f"Opportunità per servizio {opp_code}",
            "phase": 53002,
            "category": 25309,
            "status": 1,
            "salesPersons": [int(ticket.owner_id)],
            "budget": 0,
            "amount": 0,
            "closeDate": datetime.utcnow().isoformat()
        }

        print("🔥 PAYLOAD OPPORTUNITY:", payload)

        response = create_crm_opportunity(payload)

        if not response or not isinstance(response, (int, str)):
            raise Exception(f"Errore creazione opportunità CRM: {response}")

        try:
            opportunity_id = int(response)
        except Exception as e:
            raise Exception(f"Errore parsing ID opportunità CRM: {response}") from e

        new_ticket = Ticket(
            ticket_code=f"{opp_code}-{opportunity_id}",
            title=f"Ticket per opportunità {opp_code}",
            description="Creato da opportunità CRM",
            customer_name=ticket.customer_name,
            priority=2,
            status=0,
            owner=ticket.owner,
            owner_id=ticket.owner_id,
            activity_id=ticket.activity_id  # ✅ usa lo stesso activity_id del ticket di origine
        )
        db_session.add(new_ticket)
        db_session.flush()

        first_task = Task(
            title=f"Task iniziale {opp_code}",
            ticket_id=new_ticket.id,
            status="aperto",
            priority="media",
            owner=ticket.owner_id,
        )
        db_session.add(first_task)
        db_session.commit()

        created.append({
            "opportunity": opp_code,
            "opportunity_id": opportunity_id,
            "ticket_id": new_ticket.id,
            "task_id": first_task.id,
        })

    return created
