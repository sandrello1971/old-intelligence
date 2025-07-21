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

DEFAULT_ACTIVITY_SUBTYPE = 63705
DEFAULT_ACTIVITY_PRIORITY = 0  # compatibile con CRM (0 = "bassa" se accetta interi)
DEFAULT_ACTIVITY_STATE = 2  # completata


def create_and_sync_opportunities(ticket: Ticket, db_session=None):
    if db_session is None:
        db_session = SessionLocal()

    if not ticket.customer_name:
        raise Exception(f"Ticket ID {ticket.id} - Manca il nome dell'azienda (customer_name).")

    if not ticket.owner:
        raise Exception(f"Ticket ID {ticket.id} - Manca il nome dell'owner.")

    # Recupera l'azienda
    company = db_session.query(Company).filter(Company.nome == ticket.customer_name.strip()).first()
    if not company:
        raise Exception(f"Azienda '{ticket.customer_name}' non trovata nella tabella companies. Impossibile ottenere il crossId.")

    # Recupera descrizione e servizi
    description = ""
    services = []

    if ticket.activity:
        description = ticket.activity.description or ""
        services = ticket.activity.detected_services or []

    if not description:
        description = ticket.description or ""

    print(f"🔎 Descrizione usata per estrazione: {description}")
    print(f"🔎 Servizi rilevati: {services}")

    opportunities = extract_opportunities_from_description(description, services)
    print(f"🔧 Opportunità rilevate: {opportunities}")

    created = []

    for opp_code in opportunities:
        opportunity_code = f"{opp_code}-{ticket.id}"

        existing_opp = db_session.query(Opportunity).filter(
            Opportunity.codice == opportunity_code,
            Opportunity.cliente == ticket.customer_name
        ).first()
        if existing_opp:
            print(f"⚠️ Opportunità {opportunity_code} per {ticket.customer_name} già esistente, skip.")
            continue

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
            "closeDate": datetime.utcnow().isoformat(),
            "code": opportunity_code
        }

        print("🔥 PAYLOAD OPPORTUNITY:", payload)

        response = create_crm_opportunity(payload)

        if not response or not isinstance(response, (int, str)):
            raise Exception(f"Errore creazione opportunità CRM: {response}")

        try:
            opportunity_id = int(response)
        except Exception as e:
            raise Exception(f"Errore parsing ID opportunità CRM: {response}") from e

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

    return {
        "created_opportunities": created,
        "count": len(created)
    }

def generate_activities_from_opportunity(opportunity_id: int, db_session=None):
    from app.models.opportunity import Opportunity
    from app.models.company import Company
    from app.models.milestone import Milestone
    from app.models.activity import Activity
    from app.models.ticket import Ticket
    from app.models.task import Task
    from app.models.phase_template import PhaseTemplate
    from app.core.database import SessionLocal
    from integrations.crm_incloud.activity import create_crm_activity
    from datetime import datetime

    DEFAULT_ACTIVITY_SUBTYPE = 63705
    DEFAULT_ACTIVITY_PRIORITY = 0
    DEFAULT_ACTIVITY_STATE = 2

    print(f"🔁 Avvio generazione attività da opportunità ID: {opportunity_id}")

    if db_session is None:
        db_session = SessionLocal()

    opportunity = db_session.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opportunity:
        print(f"❌ Opportunità ID {opportunity_id} non trovata nel database")
        raise Exception(f"Opportunità con ID {opportunity_id} non trovata.")

    company = db_session.query(Company).filter(Company.nome == opportunity.cliente).first()
    if not company:
        print(f"❌ Azienda '{opportunity.cliente}' non trovata nel database")
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

        crm_payload = {
            "title": milestone.name,
            "activityDate": datetime.utcnow().isoformat(),
            "activityEndDate": datetime.utcnow().isoformat(),
            "allDay": False,
            "classification": 0,
            "commercial": False,
            "companyId": company.id,
            "createdById": opportunity.commerciale,
            "createdDate": datetime.utcnow().isoformat(),
            "duration": 0,
            "opportunityId": opportunity.id,
            "ownerId": opportunity.commerciale,
            "priority": DEFAULT_ACTIVITY_PRIORITY,
            "state": DEFAULT_ACTIVITY_STATE,
            "subject": f"{milestone.name} ({milestone.project_type})",
            "toDo": 1,
            "type": 7,
            "subTypeId": DEFAULT_ACTIVITY_SUBTYPE,
            "idCompanion": int(opportunity.commerciale)
        }

        try:
            crm_result = create_crm_activity(crm_payload)
            print(f"🟢 Attività CRM creata con ID: {crm_result}")
        except Exception as e:
            print(f"❌ Errore invio attività CRM: {e}")

        suffix = str(activity.id)[-4:]
        ticket_code = f"TCK-{opp_code}-{suffix}-{i:02}"

        ticket = Ticket(
            activity_id=activity.id,
            ticket_code=ticket_code,
            title=milestone.name,
            description="Creato da fasi CRM",
            customer_name=company.nome,
            priority=2,
            status=0,
            owner=opportunity.proprietario,
            owner_id=opportunity.commerciale
        )
        db_session.add(ticket)
        db_session.flush()

        task = Task(
            title=f"Task iniziale {opp_code} - {milestone.name}",
            ticket_id=ticket.id,
            status="aperto",
            priority="media",
            owner=opportunity.commerciale
        )
        db_session.add(task)

        created_activities.append(activity.id)

    db_session.commit()
    print(f"✅ Attività generate: {created_activities}")
    return {"created_activities": created_activities}
