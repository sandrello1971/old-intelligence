from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.milestone import Milestone  # ⬅️ Import CRUCIALE

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
    owner = Column(String, ForeignKey("owners.id"))
    milestone_id = Column(Integer, ForeignKey("milestones.id"))
    customer_name = Column(String)

    predecessor_ref = relationship("Task", remote_side=[id], foreign_keys=[predecessor_id], backref="next_tasks")
    parent_ref = relationship("Task", remote_side=[id], foreign_keys=[parent_id], backref="child_tasks")

    # ✅ La riga che mancava:
    milestone = relationship("Milestone", back_populates="tasks")
    hashtags: list[HashtagSchema] = []
