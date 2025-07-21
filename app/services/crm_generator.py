from sqlalchemy.orm import Session
from app.models.ticket import Ticket
from app.models.activity import Activity
from app.models.task import Task
from app.models.opportunity import Opportunity
from app.models.milestone import Milestone
from app.services.crm_parser import extract_opportunities_from_description
from integrations.crm_incloud.activity import create_crm_activity

DEFAULT_ACTIVITY_SUBTYPE = 63705
DEFAULT_ACTIVITY_PRIORITY = 0  # compatibile con CRM (0 = "bassa" se accetta interi)
DEFAULT_ACTIVITY_STATE = 2  # completata

def generate_opportunities_for_activity(activity_id: int, db: Session):
    activity = db.query(Activity).filter_by(id=activity_id).first()
    if not activity:
        raise ValueError(f"Attività ID {activity_id} non trovata.")

    opportunities = extract_opportunities_from_description(activity.description, activity.detected_services)

    created = {
        "opportunities": [],
        "activities": [],
        "tickets": [],
        "tasks": []
    }

    for opportunity_code in opportunities:
        opportunity = Opportunity(
            title=f"Opportunità per {opportunity_code}",
            description=activity.description or "Generata automaticamente",
            status="nuova",
            activity_id=activity.id,
            customer_id=activity.customer_id,
            company_id=activity.company_id
        )
        db.add(opportunity)
        db.flush()
        created["opportunities"].append(opportunity.id)

        # Associa le milestones
        milestones = db.query(Milestone).filter(Milestone.project_type == opportunity_code).order_by(Milestone.order).all()
        
        for milestone in milestones:
            # Creazione dell'attività per ogni milestone
            milestone_activity = Activity(
                opportunity_id=opportunity.id,
                milestone_id=milestone.id,
                project_type=opportunity_code,
                company_id=activity.company_id,
                status="aperta",
                sub_type_id=DEFAULT_ACTIVITY_SUBTYPE,
                accompagnato_da=str(activity.owner_id),
                accompagnato_da_nome=activity.owner_name
            )
            db.add(milestone_activity)
            db.flush()

            # Creazione dei ticket per ogni milestone
            ticket = Ticket(
                activity_id=milestone_activity.id,
                ticket_code=f"TCK-{opportunity_code}-{milestone.id}",
                title=f"Ticket {milestone.name} - {opportunity_code}",
                description=milestone.name,
                priority=2,
                gtd_type="Project",
                customer_name=activity.customer_name,
                owner_id=activity.owner_id
            )
            db.add(ticket)
            db.flush()
            created["tickets"].append(ticket.id)

            # Creazione dei task per ogni ticket
            tasks = db.query(Task).filter(Task.milestone_id == milestone.id).all()
            for task in tasks:
                task_ticket = Task(
                    title=f"Task {task.title} - {milestone.name}",
                    ticket_id=ticket.id,
                    status="aperto",
                    priority=2,
                    owner=activity.owner_name
                )
                db.add(task_ticket)
                created["tasks"].append(task_ticket.id)

    db.commit()
    return created
