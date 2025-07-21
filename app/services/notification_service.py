from app.services.email_service import email_service
from app.services.opportunity_creator import get_service_owner
from app.models.user import User
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

def send_ticket_notification(ticket_id: int, db: Session) -> bool:
    """Invia notifica creazione ticket"""
    try:
        # Importa qui per evitare circular import
        from app.models.ticket import Ticket
        
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            return False
        
        # Determina owner
        owner_id = None
        if ticket.opportunity_code:
            owner_id = get_service_owner(ticket.opportunity_code, db)
        
        if not owner_id:
            owner_id = ticket.owner
            
        if not owner_id:
            return False
            
        # Get user email
        owner = db.query(User).filter(User.id == owner_id).first()
        if not owner or not owner.email:
            return False
            
        # Send email
        return email_service.send_email(
            to_email=owner.email,
            subject=f"Nuovo Ticket - {ticket.title}",
            html_body=f"""
            <h2>Intelligence Platform - Nuovo Ticket</h2>
            <p><strong>Titolo:</strong> {ticket.title}</p>
            <p><strong>Codice:</strong> {ticket.code}</p>
            <p><strong>Cliente:</strong> {ticket.customer_name or 'N/A'}</p>
            <p><a href="https://intelligence.enduser-digital.com/dashboard/">Vai alla Dashboard</a></p>
            """,
            text_body=f"Nuovo ticket: {ticket.title} ({ticket.code}) - Cliente: {ticket.customer_name or 'N/A'}"
        )
        
    except Exception as e:
        logger.error(f"Error sending ticket notification: {e}")
        return False
