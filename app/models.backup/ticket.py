from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, ARRAY, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.associations import ticket_hashtag
from app.models.hashtag import Hashtag
from app.models.milestone import Milestone

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=True)
    ticket_code = Column(String)
    title = Column(String)
    description = Column(Text)
    priority = Column(Integer)
    status = Column(Integer)
    due_date = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)
    parent_id = Column(Integer)
    owner_id = Column(Integer)
    gtd_type = Column(Integer)
    assigned_to = Column(Integer)
    owner = Column(String)
    milestone_id = Column(Integer, ForeignKey("milestones.id"), nullable=True)
    customer_name = Column(String)
    gtd_generated = Column(Boolean, default=False)
    account = Column(String, nullable=True)
    
    hashtags = relationship("Hashtag", secondary=ticket_hashtag, backref="tickets")
    tasks = relationship("Task", back_populates="ticket")
    activity = relationship("Activity", back_populates="tickets")
    milestone = relationship("Milestone", back_populates="tickets")
    company_id = Column(Integer, ForeignKey("companies.id"))
    company = relationship("Company", backref="tickets")
    detected_services = Column(ARRAY(String), nullable=True)
