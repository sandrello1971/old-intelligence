# app/routes/opportunities.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.opportunity_creator import create_and_sync_opportunities, generate_activities_from_opportunity
from app.models.activity import Activity
from app.models.task import Task
from app.models.ticket import Ticket
from app.services.i24_commessa import create_commessa_from_activity

router = APIRouter(tags=["opportunities"])


@router.post("/opportunities/from-task/{task_id}")
def generate_opportunities_from_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task non trovato")

    ticket = db.query(Ticket).filter(Ticket.id == task.ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trovato")

    return create_and_sync_opportunities(ticket, db)


@router.post("/opportunities/{opportunity_id}/generate-activities")
def generate_activities_for_opportunity(opportunity_id: int, db: Session = Depends(get_db)):
    print(f"🔁 Avvio generazione attività da opportunità ID: {opportunity_id}")
    try:
        result = generate_activities_from_opportunity(opportunity_id, db)
        print(f"✅ Risultato: {result}")
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")


@router.post("/commessa/i24/{activity_id}")
def create_commessa_i24(activity_id: int, db: Session = Depends(get_db)):
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Attività non trovata")

    try:
        result = create_commessa_from_activity(activity.id, db)
        return {"message": "Commessa I24 creata", **result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
