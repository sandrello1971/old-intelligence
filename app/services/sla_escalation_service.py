from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.task import Task
from app.models.user import User
from app.models.phase_template import PhaseTemplate
from app.core.database import SessionLocal
import logging

logger = logging.getLogger(__name__)

class SLAEscalationService:
    
    def check_overdue_tasks(self, db: Session = None) -> dict:
        """Controlla task scaduti e invia escalation se necessario"""
        if db is None:
            db = SessionLocal()
            
        try:
            now = datetime.utcnow()
            
            # Trova tutti i task aperti scaduti
            overdue_tasks = db.query(Task).filter(
                Task.status != "chiuso",
                Task.due_date < now
            ).all()
            
            escalations_sent = 0
            warnings_sent = 0
            
            for task in overdue_tasks:
                days_overdue = (now - task.due_date).days
                
                # Estrai description base per JOIN con template
                base_description = task.description
                if " --- DETTAGLI:" in task.description:
                    base_description = task.description.split(" --- DETTAGLI:")[0]
                
                # Trova template per ottenere escalation_days
                template = db.query(PhaseTemplate).filter(
                    PhaseTemplate.description == base_description
                ).first()
                
                escalation_days = getattr(template, 'escalation_days', 3) if template else 3
                warning_days = getattr(template, 'warning_days', 2) if template else 2
                
                logger.info(f"Task {task.id}: {days_overdue} giorni di ritardo, escalation_days: {escalation_days}")
                
                # Escalation se ritardo >= escalation_days
                if days_overdue >= escalation_days:
                    if self._send_escalation_email(task, days_overdue, db):
                        escalations_sent += 1
                        logger.info(f"Escalation sent for task {task.id} - {days_overdue} days overdue")
            
            return {
                "checked_tasks": len(overdue_tasks),
                "escalations_sent": escalations_sent,
                "timestamp": now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in escalation check: {e}")
            return {"error": str(e)}
        finally:
            if db:
                db.close()
    
    def check_warning_tasks(self, db: Session = None) -> dict:
        """Controlla task prossimi alla scadenza per warning"""
        if db is None:
            db = SessionLocal()
            
        try:
            now = datetime.utcnow()
            
            # Trova task che scadranno presto (prossimi 2 giorni)
            warning_tasks = db.query(Task).filter(
                Task.status != "chiuso",
                Task.due_date > now,
                Task.due_date <= now + timedelta(days=2)
            ).all()
            
            warnings_sent = 0
            
            for task in warning_tasks:
                days_until_due = (task.due_date - now).days
                
                # Estrai description base
                base_description = task.description
                if " --- DETTAGLI:" in task.description:
                    base_description = task.description.split(" --- DETTAGLI:")[0]
                
                # Trova template
                template = db.query(PhaseTemplate).filter(
                    PhaseTemplate.description == base_description
                ).first()
                
                warning_days = getattr(template, 'warning_days', 2) if template else 2
                
                # Warning se mancano <= warning_days alla scadenza
                if days_until_due <= warning_days:
                    if self._send_warning_email(task, days_until_due, db):
                        warnings_sent += 1
                        logger.info(f"Warning sent for task {task.id} - {days_until_due} days until due")
            
            return {
                "checked_tasks": len(warning_tasks),
                "warnings_sent": warnings_sent,
                "timestamp": now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in warning check: {e}")
            return {"error": str(e)}
        finally:
            if db:
                db.close()
    
    def _send_escalation_email(self, task: Task, days_overdue: int, db: Session) -> bool:
        """Invia email di escalation per task scaduto"""
        try:
            from app.services.email_service import email_service
            
            # Trova owner del task
            owner = db.query(User).filter(User.id == str(task.owner)).first()
            if not owner or not owner.email:
                logger.warning(f"No owner or email for task {task.id}")
                return False
            
            # Email escalation
            subject = f"🚨 ESCALATION - Task Scaduto: {task.title}"
            
            html_body = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                    <h1 style="margin: 0;">🚨 ESCALATION TASK</h1>
                    <h2 style="margin: 10px 0 0 0;">Task Scaduto da {days_overdue} giorni</h2>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px;">
                    <p>Ciao <strong>{owner.name}</strong>,</p>
                    <p><strong>⚠️ ATTENZIONE:</strong> Il seguente task è scaduto da <strong>{days_overdue} giorni</strong> e richiede intervento immediato:</p>
                    
                    <div style="background: white; border-radius: 8px; padding: 20px; margin: 20px 0; border-left: 4px solid #dc3545;">
                        <h3 style="margin-top: 0; color: #dc3545;">{task.title}</h3>
                        <p><strong>Cliente:</strong> {task.customer_name or 'N/A'}</p>
                        <p><strong>Scadenza originale:</strong> {task.due_date.strftime('%d/%m/%Y %H:%M') if task.due_date else 'N/A'}</p>
                        <p><strong>Giorni di ritardo:</strong> <span style="color: #dc3545; font-weight: bold;">{days_overdue} giorni</span></p>
                        <p><strong>Priorità:</strong> {task.priority or 'Media'}</p>
                    </div>
                    
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="https://intelligence.enduser-digital.com/dashboard/task/{task.id}" 
                           style="background: #dc3545; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                            🚨 GESTISCI TASK ESCALATION
                        </a>
                    </p>
                    
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                    <p style="font-size: 12px; color: #666;">
                        Questa è un'email automatica di escalation per task scaduti. Contatta il team se necessario.
                    </p>
                </div>
            </div>
            """
            
            success = email_service.send_email(
                to_email=owner.email,
                subject=subject,
                html_body=html_body,
                text_body=f"ESCALATION - Task '{task.title}' scaduto da {days_overdue} giorni. Link: https://intelligence.enduser-digital.com/dashboard/task/{task.id}"
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending escalation email for task {task.id}: {e}")
            return False
    
    def _send_warning_email(self, task: Task, days_until_due: int, db: Session) -> bool:
        """Invia email di warning per task in scadenza"""
        try:
            from app.services.email_service import email_service
            
            # Trova owner del task
            owner = db.query(User).filter(User.id == str(task.owner)).first()
            if not owner or not owner.email:
                logger.warning(f"No owner or email for task {task.id}")
                return False
            
            # Email warning
            subject = f"⚠️ WARNING - Task in Scadenza: {task.title}"
            
            html_body = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #ffc107 0%, #e0a800 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                    <h1 style="margin: 0;">⚠️ WARNING TASK</h1>
                    <h2 style="margin: 10px 0 0 0;">Task in Scadenza tra {days_until_due} giorni</h2>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px;">
                    <p>Ciao <strong>{owner.name}</strong>,</p>
                    <p><strong>⚠️ PROMEMORIA:</strong> Il seguente task scadrà tra <strong>{days_until_due} giorni</strong>:</p>
                    
                    <div style="background: white; border-radius: 8px; padding: 20px; margin: 20px 0; border-left: 4px solid #ffc107;">
                        <h3 style="margin-top: 0; color: #e0a800;">{task.title}</h3>
                        <p><strong>Cliente:</strong> {task.customer_name or 'N/A'}</p>
                        <p><strong>Scadenza:</strong> {task.due_date.strftime('%d/%m/%Y %H:%M') if task.due_date else 'N/A'}</p>
                        <p><strong>Giorni rimanenti:</strong> <span style="color: #e0a800; font-weight: bold;">{days_until_due} giorni</span></p>
                        <p><strong>Priorità:</strong> {task.priority or 'Media'}</p>
                    </div>
                    
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="https://intelligence.enduser-digital.com/dashboard/task/{task.id}" 
                           style="background: #ffc107; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                            ⚠️ GESTISCI TASK
                        </a>
                    </p>
                    
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                    <p style="font-size: 12px; color: #666;">
                        Questo è un promemoria automatico per task in scadenza.
                    </p>
                </div>
            </div>
            """
            
            success = email_service.send_email(
                to_email=owner.email,
                subject=subject,
                html_body=html_body,
                text_body=f"WARNING - Task '{task.title}' scade tra {days_until_due} giorni. Link: https://intelligence.enduser-digital.com/dashboard/task/{task.id}"
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending warning email for task {task.id}: {e}")
            return False

# Istanza singleton
sla_escalation_service = SLAEscalationService()
