from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class PhaseTemplate(Base):
    __tablename__ = "phase_templates"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, nullable=False)
    type = Column(String, nullable=False)
    description = Column(String, nullable=False)
    milestone_id = Column(Integer, ForeignKey("milestones.id"), nullable=True)  # ✅ milestones corretto
    order = Column(Integer, nullable=True)  # ✅ ordine delle fasi
    parent_id = Column(Integer, ForeignKey("phase_templates.id"), nullable=True)  # ✅ struttura gerarchica (figlio/genitore)

    milestone = relationship("Milestone", back_populates="phases", foreign_keys=[milestone_id])
    children = relationship("PhaseTemplate", backref="parent", remote_side=[id])
