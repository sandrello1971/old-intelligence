from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP, func
from app.core.database import Base

class CrmLink(Base):
    __tablename__ = "crm_links"

    id = Column(Integer, primary_key=True, index=True)
    local_ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"))
    crm_opportunity_id = Column(Integer, nullable=False)
    crm_activity_id = Column(Integer, nullable=False)
    crm_company_id = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
