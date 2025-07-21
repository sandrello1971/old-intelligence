from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class PhaseTemplate(Base):
    __tablename__ = "phase_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, nullable=False)
    type = Column(String, nullable=False)
    description = Column(String, nullable=False)
    milestone_id = Column(Integer, ForeignKey("milestones.id"), nullable=True)
    order = Column(Integer, nullable=True)
    parent_id = Column(Integer, ForeignKey("phase_templates.id"), nullable=True)
    sla_days = Column(Integer, nullable=True, default=3)
    warning_days = Column(Integer, nullable=True, default=2)
    escalation_days = Column(Integer, nullable=True, default=1)
    detailed_description = Column(String, nullable=True)
    
    milestone = relationship("Milestone", back_populates="phases", foreign_keys=[milestone_id])
    children = relationship("PhaseTemplate", backref="parent", remote_side=[id])
