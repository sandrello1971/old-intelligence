from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class ServiceUserAssociation(Base):
    __tablename__ = "service_user_associations"
    
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("sub_types.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False, default="responsible")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships (opzionali se gli altri modelli non le hanno)
    # service = relationship("SubType", back_populates="user_associations")
    # user = relationship("LocalUser", back_populates="service_associations")
