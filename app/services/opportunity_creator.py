from datetime import datetime, timedelta
from pprint import pprint
import json
import logging

logger = logging.getLogger(__name__)

from app.services.crm_parser import extract_opportunities_from_description, extract_services_from_description
from integrations.crm_incloud.opportunity import create_crm_opportunity
from integrations.crm_incloud.activity import create_crm_activity
from integrations.crm_incloud.sync import sync_single_activity
from app.models.ticket import Ticket
from app.models.company import Company
from app.models.opportunity import Opportunity
from app.models.activity import Activity
from app.models.milestone import Milestone
from app.models.phase_template import PhaseTemplate
from app.models.service_user_association import ServiceUserAssociation
from app.models.task import Task
from app.core.database import SessionLocal

DEFAULT_ACTIVITY_SUBTYPE = 63705
DEFAULT_ACTIVITY_PRIORITY = 0
DEFAULT_ACTIVITY_STATE = 2

def get_service_owner(service_code: str, db_session):
    """Trova l'owner di un servizio dalle associazioni"""
    try:
        # Importa SubType per il join (potrebbe non essere già importato)
        from app.models.sub_type import SubType
        
        association = db_session.query(ServiceUserAssociation).join(
            SubType, ServiceUserAssociation.service_id == SubType.id
        ).filter(SubType.code == service_code).first()
        
        if association:
            print(f"✅ Owner trovato per servizio {service_code}: {association.user_id}")
            return association.user_id
        else:
            print(f"⚠️ Nessuna associazione trovata per servizio {service_code}")
            return None
    except Exception as e:
        print(f"❌ Errore ricerca owner per {service_code}: {e}")
        return None

def send_ticket_notification(ticket_id: int, db_session) -> bool:
    """Invia notifica creazione ticket"""
    try:
        from app.services.email_service import email_service
        from app.models.user import User
        
        ticket = db_session.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            logger.error(f"Ticket {ticket_id} not found for notification")
            return False
        
        # Determina owner dal ticket
        owner_id = ticket.owner_id
        if not owner_id:
            logger.error(f"No owner found for ticket {ticket_id}")
            return False
            
        # Get user email
        owner = db_session.query(User).filter(User.id == str(owner_id)).first()
        if not owner or not owner.email:
            logger.error(f"Owner {owner_id} not found or no email for ticket {ticket_id}")
            return False
        
        # Determina tipo servizio dal ticket code per personalizzare email
        service_type = "Servizio"
        service_color = "#667eea"  # Default blue
        if ticket.ticket_code and "KHW" in ticket.ticket_code:
            service_type = "Know How"
            service_color = "#28a745"  # Green
        elif ticket.ticket_code and "PBX" in ticket.ticket_code:
            service_type = "Patent Box"
            service_color = "#17a2b8"  # Cyan
        elif ticket.ticket_code and "F40" in ticket.ticket_code:
            service_type = "Formazione 4.0"
            service_color = "#ffc107"  # Yellow
        elif ticket.ticket_code and "T50" in ticket.ticket_code:
            service_type = "Transizione 5.0"
            service_color = "#6f42c1"  # Purple
        elif ticket.ticket_code and "BND" in ticket.ticket_code:
            service_type = "Bandi"
            service_color = "#fd7e14"  # Orange
            
        # Send email
        success = email_service.send_email(
            to_email=owner.email,
            subject=f"🧠 Intelligence - Nuovo Ticket {service_type}: {ticket.title}",
            html_body=f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, {service_color} 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                    <h1 style="margin: 0;">🧠 Intelligence Platform</h1>
                    <h2 style="margin: 10px 0 0 0;">Nuovo Ticket {service_type}</h2>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px;">
                    <p>Ciao <strong>{owner.name}</strong>,</p>
                    <p>Ti è stato assegnato un nuovo ticket {service_type}:</p>
                    
                    <div style="background: white; border-radius: 8px; padding: 20px; margin: 20px 0; border-left: 4px solid {service_color};">
                        <h3 style="margin-top: 0; color: #333;">{ticket.title}</h3>
                        <p><strong>Codice:</strong> {ticket.ticket_code}</p>
                        <p><strong>Cliente:</strong> {ticket.customer_name or 'N/A'}</p>
                        <p><strong>Account:</strong> {ticket.account or 'N/A'}</p>
                        <p><strong>Priorità:</strong> {ticket.priority or 'Media'}</p>
                        <p><strong>Scadenza:</strong> {ticket.due_date.strftime('%d/%m/%Y') if ticket.due_date else 'Non specificata'}</p>
                    </div>
                    
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="https://intelligence.enduser-digital.com/dashboard/ticket/{ticket.id}" 
                           style="background: {service_color}; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                            Visualizza Ticket {service_type}
                        </a>
                    </p>
                    
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                    <p style="font-size: 12px; color: #666;">
                        Ricevi questa email perché sei il responsabile di questo ticket {service_type}.
                    </p>
                </div>
            </div>
            """,
            text_body=f"""
            Intelligence Platform - Nuovo Ticket {service_type}
            
            Ciao {owner.name},
            
            Ti è stato assegnato un nuovo ticket {service_type}:
            
            Titolo: {ticket.title}
            Codice: {ticket.ticket_code}
            Cliente: {ticket.customer_name or 'N/A'}
            Account: {ticket.account or 'N/A'}
            Priorità: {ticket.priority or 'Media'}
            Scadenza: {ticket.due_date.strftime('%d/%m/%Y') if ticket.due_date else 'Non specificata'}
            
            Visualizza: https://intelligence.enduser-digital.com/dashboard/ticket/{ticket.id}
            """
        )
        
        if success:
            logger.info(f"Email notification sent successfully for {service_type} ticket {ticket_id}")
        else:
            logger.warning(f"Email notification failed for {service_type} ticket {ticket_id}")
            
        return success
        
    except Exception as e:
        logger.error(f"Error sending ticket notification: {e}")
        return False

def create_and_sync_opportunities(ticket: Ticket, db_session=None):
    if db_session is None:
        db_session = SessionLocal()

    if not ticket.customer_name:
        raise Exception(f"Ticket ID {ticket.id} - Manca il nome dell'azienda.")
    if not ticket.owner:
        raise Exception(f"Ticket ID {ticket.id} - Manca l'owner.")
    if not ticket.activity:
        raise Exception(f"Ticket ID {ticket.id} - Nessuna attività collegata.")
    open_tasks = db_session.query(Task).filter(Task.ticket_id == ticket.id, Task.status != "chiuso").all()
    if open_tasks:
        raise Exception(f"Ticket ID {ticket.id} - Task ancora aperti: {[t.title for t in open_tasks]}")

    company = db_session.query(Company).filter(Company.nome == ticket.customer_name.strip()).first()
    if not company:
        raise Exception(f"Azienda '{ticket.customer_name}' non trovata.")

    services = ticket.activity.detected_services or []
    if isinstance(services, str):
        try:
            services = json.loads(services)
        except json.JSONDecodeError:
            services = services.replace("{", "").replace("}", "").replace('"', '').split(",")
            services = [s.strip() for s in services if s.strip()]

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
            print(f"⏽ Opportunità già esistente: {opportunity_code}")
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

        opportunity_id = int(response)

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

    # ✅ NOTE: Le opportunità sono create, i ticket derivati vengono creati in generate_activities_from_opportunity
    logger.info(f"Created {len(created)} opportunities for ticket {ticket.id}")
    return {"created_opportunities": created, "count": len(created)}

def generate_activities_from_opportunity(opportunity_id: int, db_session=None):
    print(f"🔁 Avvio generazione attività da opportunità ID: {opportunity_id}")
    if db_session is None:
        db_session = SessionLocal()

    opportunity = db_session.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opportunity:
        raise Exception(f"Opportunità con ID {opportunity_id} non trovata.")

    company = db_session.query(Company).filter(Company.nome == opportunity.cliente).first()
    if not company:
        raise Exception(f"Azienda '{opportunity.cliente}' non trovata.")

    opp_code = opportunity.codice.split("-")[0]
    milestones = db_session.query(Milestone).filter(Milestone.project_type == opp_code).order_by(Milestone.order).all()

    created_activities = []
    created_tickets = []  # ✅ LISTA per tracciare ticket creati per notifiche

    for ticket_seq, milestone in enumerate(milestones, start=1):
        # 🔄 OWNER DINAMICO: Calcola owner da associazioni
        service_owner = get_service_owner(opp_code, db_session)
        actual_owner = service_owner if service_owner else int(opportunity.commerciale)
        
        print(f"🎯 Servizio {opp_code}: Owner = {actual_owner}")
        
        # Calcola owner name e account I24
        from app.models.user import User
        owner_user = db_session.query(User).filter(User.id == str(actual_owner)).first()  
        owner_name = f"{owner_user.name} {owner_user.surname}".strip() if owner_user else "Owner Sconosciuto"
        
        # Account dall'I24 originale
        i24_ticket = db_session.query(Ticket).filter(
            Ticket.ticket_code.like("TCK-I24%"),
            Ticket.customer_name == company.nome
        ).first()
        i24_account = i24_ticket.account if i24_ticket else opportunity.proprietario
        print(f"🔧 DEBUG ACCOUNT: company={company.nome}, i24_found={bool(i24_ticket)}, account={i24_account}")
        
        payload = {
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
            "description": f"Generata attività per Fase '{milestone.name}'",
            "toDo": 0,
            "type": 7,
            "subTypeId": DEFAULT_ACTIVITY_SUBTYPE,
            "idCompanion": int(opportunity.commerciale)
        }

        print("📤 Payload attività CRM:")
        pprint(payload)
        try:
            print("📤 DEBUG PAYLOAD COMPLETO:")
            pprint(payload)
            print("🔍 Subject presente:", "subject" in payload)
            print("🔍 Subject valore:", payload.get("subject", "MISSING"))
            crm_activity_id = create_crm_activity(payload)
            print(f"🟢 Attività CRM creata: {crm_activity_id}")
        except Exception as e:
            print(f"❌ Errore attività CRM: {e}")
            continue

        activity = sync_single_activity(int(crm_activity_id), db_session)
        if activity:
            created_activities.append(activity.id)

            suffix = str(activity.id)[-4:]
            ticket_code = f"TCK-{opp_code}-{suffix}-{ticket_seq:02}"

            ticket = Ticket(
                activity_id=activity.id,
                ticket_code=ticket_code,
                title=f"{milestone.name} - {ticket_code}",
                description="Creato da Fase CRM",
                customer_name=company.nome,
                priority=2,
                status=0,
                owner=owner_name,
                owner_id=str(actual_owner),
                account=i24_account,  
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                due_date=datetime.utcnow() + timedelta(days=getattr(milestone, "sla_days", 5)),
                company_id=company.id,
            )

            db_session.add(ticket)
            db_session.flush()
            
            # ✅ AGGIUNGI alla lista per notifiche
            created_tickets.append(ticket.id)

            task_templates = db_session.query(PhaseTemplate).filter(PhaseTemplate.milestone_id == milestone.id).order_by(PhaseTemplate.order.asc()).all()
            for task_template in task_templates:
                # USA SLA DINAMICO DALLA MILESTONE CORRENTE
                task_due_date = datetime.utcnow() + timedelta(days=getattr(task_template, "sla_days", 3))
                
                task = Task(
                    ticket_id=ticket.id,
                    title=task_template.description,
                    status="aperto",
                    priority="media",
                    owner=opportunity.commerciale,
                    customer_name=company.nome,
                    description=task_template.description + (" --- DETTAGLI: " + task_template.detailed_description if getattr(task_template, "detailed_description", "") else ""),
                    due_date=task_due_date,
                    milestone_id=milestone.id,
                    order=task_template.order or 1,
                )
                db_session.add(task)

    db_session.commit()
    
    # ✅ INVIO NOTIFICHE EMAIL PER TUTTI I TICKET CREATI
    for ticket_id in created_tickets:
        try:
            if send_ticket_notification(ticket_id, db_session):
                logger.info(f"Email notification sent for derived ticket {ticket_id}")
            else:
                logger.warning(f"Failed to send email notification for derived ticket {ticket_id}")
        except Exception as e:
            logger.error(f"Error sending notification for derived ticket {ticket_id}: {e}")
    
    logger.info(f"Generated {len(created_activities)} activities and sent {len(created_tickets)} email notifications")
    return {"created_activities": created_activities}
