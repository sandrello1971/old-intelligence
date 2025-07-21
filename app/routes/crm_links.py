from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.crm_link import CrmLink
from pydantic import BaseModel

router = APIRouter(tags=["CRM Links"])

class CrmLinkCreateSchema(BaseModel):
    local_ticket_id: int
    crm_opportunity_id: int
    crm_activity_id: int
    crm_company_id: int

@router.post("/crm-links")
def create_crm_link(link: CrmLinkCreateSchema, db: Session = Depends(get_db)):
    new_link = CrmLink(
        local_ticket_id=link.local_ticket_id,
        crm_opportunity_id=link.crm_opportunity_id,
        crm_activity_id=link.crm_activity_id,
        crm_company_id=link.crm_company_id
    )
    db.add(new_link)
    db.commit()
    db.refresh(new_link)
    return {"status": "success", "link_id": new_link.id}
