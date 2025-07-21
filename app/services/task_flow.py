# /app/services/task_flow.py

from app.models.task import Task
from app.models.ticket import Ticket
from app.services.opportunity_creator import create_and_sync_opportunities
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


def process_task_closure(task: Task, db_session: Session):
    """
    Gestisce logiche alla chiusura di un task.
    Se il task è l'ultimo aperto del suo ticket, genera le opportunità successive.
    """
    if task.status != "chiuso":
        logger.info(f"🟡 Task ID {task.id} non chiuso, nessuna azione.")
        return

    # Recupera tutti i task associati al ticket
    ticket_tasks = db_session.query(Task).filter(Task.ticket_id == task.ticket_id).all()
    other_open_tasks = [t for t in ticket_tasks if t.status != "chiuso" and t.id != task.id]

    if other_open_tasks:
        logger.info(f"🟡 Ci sono ancora task aperti per il ticket ID {task.ticket_id}.")
        return

    # Se non ci sono più task aperti, procedi
    ticket = db_session.query(Ticket).filter(Ticket.id == task.ticket_id).first()
    if not ticket:
        logger.warning(f"⚠️ Ticket non trovato per Task ID {task.id}.")
        return

    # Crea nuove opportunità a partire dal ticket
    created_opps = create_and_sync_opportunities(ticket, db_session)

    logger.info(f"✅ Opportunità create da Ticket ID {ticket.id}: {created_opps}")


# IMPORTANTE: in /app/routes/tasks.py
# Devi avere solo: 
# process_task_closure(task, db) dopo il commit e il refresh del task
