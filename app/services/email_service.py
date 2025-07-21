import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging
from app.core.config import SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, DEFAULT_FROM_EMAIL, ESCALATION_EMAIL

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.sender_email = DEFAULT_FROM_EMAIL
        self.sender_password = SMTP_PASSWORD
        self.escalation_email = ESCALATION_EMAIL
        
    def send_email(self, to_email: str, subject: str, html_body: str, text_body: Optional[str] = None) -> bool:
        if not self.sender_password:
            logger.warning("SMTP password not configured")
            return False
            
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"Intelligence Platform <{self.sender_email}>"
            message["To"] = to_email
            
            if text_body:
                text_part = MIMEText(text_body, "plain", "utf-8")
                message.attach(text_part)
            
            html_part = MIMEText(html_body, "html", "utf-8")
            message.attach(html_part)
            
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, [to_email], message.as_string())
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

email_service = EmailService()
