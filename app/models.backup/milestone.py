# app/models/milestone.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Milestone(Base):
    __tablename__ = "milestones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    project_type = Column(String, nullable=False)  # es: 'F40', 'T50', 'KHW'
    order = Column(Integer, nullable=False)

    tasks = relationship("Task", back_populates="milestone")
    phases = relationship("PhaseTemplate", back_populates="milestone")
    tickets = relationship("Ticket", back_populates="milestone")

