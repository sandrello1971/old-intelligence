from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.milestone import Milestone
from app.models.ticket import Ticket
from app.models.owner import Owner
from app.models.associations import task_hashtag

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    status = Column(String)
    priority = Column(String)
    due_date = Column(DateTime)
    description = Column(Text)
    predecessor_id = Column(Integer, ForeignKey("tasks.id"))
    parent_id = Column(Integer, ForeignKey("tasks.id"))
    owner = Column(String, ForeignKey("owners.id"))  # VARCHAR coerente col DB
    milestone_id = Column(Integer, ForeignKey("milestones.id"))
    customer_name = Column(String)
    closed_at = Column(DateTime, nullable=True)
    order = Column(Integer, nullable=True)
    hashtags = relationship("Hashtag", secondary=task_hashtag, backref="tasks")
    # ✅ RELAZIONI ORM
    ticket = relationship("Ticket", back_populates="tasks")
    milestone = relationship("Milestone", back_populates="tasks")
    owner_ref = relationship("Owner", back_populates="tasks_owned")
    predecessor_ref = relationship("Task", remote_side=[id], foreign_keys=[predecessor_id], backref="next_tasks")
    parent_ref = relationship("Task", remote_side=[id], foreign_keys=[parent_id], backref="child_tasks")
