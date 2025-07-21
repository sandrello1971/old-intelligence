from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
from app.models.sub_type import SubType
from sqlalchemy import Column, String

class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)
    status = Column(String, nullable=True)
    priority = Column(String, nullable=True)
    owner_id = Column(String, nullable=True)
    owner_name = Column(String, nullable=True)
    customer_id = Column(String, nullable=True)
    customer_name = Column(String, nullable=True)
    account_name = Column(String, nullable=True)
    activity_type = Column(String, nullable=True)
    creation_date = Column(String, nullable=True)
    last_modified_date = Column(String, nullable=True)
    ticket_number = Column(String, nullable=True)
    ticket_date = Column(String, nullable=True)
    has_end_date = Column(Boolean, default=False)
    last_synced = Column(String, nullable=True)
    opportunity_id = Column(String, nullable=True)
    company_id = Column(String, ForeignKey("companies.id"), nullable=True)
    email_subject = Column(String, nullable=True)
    email_approved = Column(String, nullable=True)
    approved_by = Column(String, nullable=True)
    approval_date = Column(String, nullable=True)
    due_date = Column(DateTime, nullable=True)
    ticket_id = Column(String, nullable=True)
    predicted_ticket = Column(Integer, default=0)
    ticket_code = Column(String, nullable=True)
    gtd_generated = Column(Integer, default=0)
    accompagnato_da = Column(String, nullable=True)
    sub_type_id = Column(Integer, ForeignKey("sub_types.id"), nullable=True)
    accompagnato_da_nome = Column(String, nullable=True)
    sub_type = relationship("SubType", backref="activities")
    tickets = relationship("Ticket", back_populates="activity", cascade="all, delete-orphan")
    detected_services = Column(String, nullable=True)
    milestone_id = Column(Integer, ForeignKey("milestones.id"), nullable=False)
    project_type = Column(String)

