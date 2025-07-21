from datetime import datetime
from app.services.crm_parser import extract_opportunities_from_description
from integrations.crm_incloud.opportunity import create_crm_opportunity
from app.models.ticket import Ticket
from app.models.company import Company
from app.models.opportunity import Opportunity
from app.models.activity import Activity
from app.models.milestone import Milestone
from app.models.phase_template import PhaseTemplate
from app.models.task import Task
from app.core.database import SessionLocal
from integrations.crm_incloud.activity import create_crm_activity
from app.services.i24_commessa import create_commessa_from_activity
import json
from pprint import pprint

DEFAULT_ACTIVITY_SUBTYPE = 63705
DEFAULT_ACTIVITY_PRIORITY = 0  # compatibile con CRM (0 = "bassa" se accetta interi)
DEFAULT_ACTIVITY_STATE = 2  # completata

def create_and_sync_opportunities(ticket: Ticket, db_session=None):
    if db_session is None:
        db_session = SessionLocal()

    if not ticket.customer_name:
        raise Exception(f"Ticket ID {ticket.id} - Manca il nome dell'azienda.")

    if not ticket.owner:
        raise Exception(f"Ticket ID {ticket.id} - Manca l'owner.")

    if not ticket.activity:
        raise Exception(f"Ticket ID {ticket.id} - Nessuna attività collegata.")

    # Assicura che tutti i task siano chiusi
    open_tasks = db_session.query(Task).join(Ticket).filter(
        Task.ticket_id == Ticket.id,
        Task.status != "chiuso"
    ).all()

    if open_tasks:
        raise Exception(f"Ticket ID {ticket.id} - Task ancora aperti: {[t.title for t in open_tasks]}")

    company = db_session.query(Company).filter(Company.nome == ticket.customer_name.strip()).first()
    if not company:
        raise Exception(f"Azienda '{ticket.customer_name}' non trovata.")

    services = ticket.activity.detected_services or []
    print(f"🎯 Servizi da processare: {services}")

    created = []

    for service in services:
        extracted_codes = extract_opportunities_from_description("", [service])
        if not extracted_codes:
            print(f"⚠️ Nessun codice rilevato per servizio: {service}")
            continue

        opp_code = extracted_codes[0]
        opportunity_code = f"{opp_code}-{ticket.id}"

        existing = db_session.query(Opportunity).filter(
            Opportunity.codice == opportunity_code,
            Opportunity.cliente == ticket.customer_name
        ).first()
        if existing:
            print(f"⏭ Opportunità già esistente: {opportunity_code}")
            continue

        payload = {
            "title": f"[{opp_code}] - {ticket.customer_name}",
            "crossId": company.id,
            "ownerId": int(ticket.activity.accompagnato_da) if ticket.activity.accompagnato_da else int(ticket.owner_id),
            "salesPersons": [int(ticket.activity.owner_id) if ticket.activity.owner_id else int(ticket.owner_id)],
            "description": f"Opportunità per servizio {opp_code}. Origine ticket: {ticket.ticket_code}",
            "phase": 53002,
            "category": 25309,
            "status": 1,
            "budget": 0,
            "amount": 0,
            "closeDate": datetime.utcnow().isoformat(),
            "code": opportunity_code
        }

        print("📤 Payload opportunità:", payload)
        response = create_crm_opportunity(payload)
        if not response or not isinstance(response, (int, str)):
            raise Exception(f"Errore CRM: risposta non valida ({response})")

        try:
            opportunity_id = int(response)
        except Exception as e:
            raise Exception(f"Errore parsing ID: {response}") from e

        local_opportunity = Opportunity(
            id=opportunity_id,
            titolo=payload["title"],
            cliente=ticket.customer_name,
            descrizione=payload["description"],
            stato=payload["status"],
            fase=payload["phase"],
            probabilita=0,
            data_chiusura=payload["closeDate"],
            data_creazione=datetime.utcnow(),
            data_modifica=datetime.utcnow(),
            proprietario=ticket.owner,
            commerciale=ticket.owner_id,
            codice=opportunity_code,
            categoria=payload["category"],
            ammontare=payload["amount"]
        )

        db_session.add(local_opportunity)
        db_session.commit()

        created.append({
            "opportunity": opportunity_code,
            "opportunity_id": opportunity_id,
            "opportunity_title": payload["title"],
            "ticket_id": ticket.id
        })

    return {"created_opportunities": created, "count": len(created)}


def get_ticket_details(ticket_id: int, db_session=None):
    if db_session is None:
        db_session = SessionLocal()

    ticket = db_session.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise Exception(f"Ticket con ID {ticket_id} non trovato.")
    detected_services = ticket.activity.detected_services or [] if ticket.activity else []

    print(f"🔎 Servizi rilevati nel ticket {ticket_id}: {detected_services}")

    return {
        "ticket_code": ticket.ticket_code,
        "title": ticket.title,
        "description": ticket.description,
        "detected_services": detected_services,
        "other_fields": ticket.other_fields if hasattr(ticket, "other_fields") else {}
    }

def generate_activities_from_opportunity(opportunity_id: int, db_session=None):
    print(f"🔁 Avvio generazione attività da opportunità ID: {opportunity_id}")

    if db_session is None:
        db_session = SessionLocal()

    opportunity = db_session.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opportunity:
        raise Exception(f"Opportunità con ID {opportunity_id} non trovata.")

    company = db_session.query(Company).filter(Company.nome == opportunity.cliente).first()
    if not company:
        raise Exception(f"Azienda '{opportunity.cliente}' non trovata nel database.")

    opp_code = opportunity.codice.split("-")[0]
    print(f"🔎 Codice opportunità: {opp_code}")

    milestones = db_session.query(Milestone).filter(Milestone.project_type == opp_code).order_by(Milestone.order).all()
    print(f"📌 Milestone trovate: {len(milestones)}")

    created_activities = []

    for i, milestone in enumerate(milestones, start=1):
        activity = Activity(
            opportunity_id=opportunity.id,
            milestone_id=milestone.id,
            project_type=opp_code,
            company_id=company.id,
            status="aperta",
            sub_type_id=DEFAULT_ACTIVITY_SUBTYPE,
            accompagnato_da=str(opportunity.commerciale),
            accompagnato_da_nome=opportunity.proprietario
        )
        db_session.add(activity)
        db_session.flush()
        from app.services.crm_parser import extract_services_from_description
        extracted_services = extract_services_from_description(ticket.description or "")
        activity.detected_services = extracted_services
        print(f"🚀 Servizi estratti e assegnati all'attività ID {activity.id}: {extracted_services}")

        tasks = db_session.query(PhaseTemplate).filter(PhaseTemplate.milestone_id == milestone.id).all()
        crm_payload = {
            "title": milestone.name,
            "activityDate": datetime.utcnow().isoformat(),
            "activityEndDate": datetime.utcnow().isoformat(),
            "allDay": False,
            "classification": 0,
            "commercial": False,
            "companyId": company.id,
            "createdById": int(opportunity.commerciale),
            "createdDate": datetime.utcnow().isoformat(),
            "duration": 0,
            "opportunityId": opportunity.id,
            "ownerId": int(opportunity.commerciale),
            "priority": DEFAULT_ACTIVITY_PRIORITY,
            "state": DEFAULT_ACTIVITY_STATE,
            "subject": f"{milestone.name} ({milestone.project_type})",
            "toDo": 1,
            "type": 7,
            "subTypeId": DEFAULT_ACTIVITY_SUBTYPE,
            "idCompanion": int(opportunity.commerciale)
        }

        try:
            print("📤 Payload CRM Activity:")
            pprint(crm_payload)
            crm_result = create_crm_activity(crm_payload)
            print(f"🟢 Attività CRM creata con ID: {crm_result}")
        except Exception as e:
            print(f"❌ Errore invio attività CRM: {e}")

        suffix = str(activity.id)[-4:]
        ticket_code = f"TCK-{opp_code}-{suffix}-{i:02}"

        ticket = Ticket(
            activity_id=activity.id,
            ticket_code=ticket_code,
            title=f"{milestone.name} - {ticket_code}",
            description="Creato da fasi CRM",
            customer_name=company.nome,
            priority=2,
            status=0,
            owner=opportunity.proprietario,
            owner_id=opportunity.commerciale
        )

        db_session.add(ticket)
        db_session.flush()

        tasks = db_session.query(PhaseTemplate).filter(PhaseTemplate.milestone_id == milestone.id).all()
        for task in tasks:
            task_entry = Task(
                title=f"{task.description}",
                ticket_id=ticket.id,
                status="aperto",
                priority="media",
                owner=opportunity.commerciale
            )
            db_session.add(task_entry)

        created_activities.append(activity.id)

    db_session.commit()
    print(f"✅ Attività generate: {created_activities}")
    return {"created_activities": created_activities}
