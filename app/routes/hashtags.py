from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.hashtag import Hashtag
from app.models.ticket import Ticket
from app.models.task import Task

router = APIRouter(prefix="/api/hashtags", tags=["hashtags"])

@router.post("/")
def create_hashtag(name: str, db: Session = Depends(get_db)):
    existing = db.query(Hashtag).filter(Hashtag.name == name).first()
    if existing:
        return existing
    hashtag = Hashtag(name=name)
    db.add(hashtag)
    db.commit()
    db.refresh(hashtag)
    return hashtag

@router.get("/")
def list_hashtags(db: Session = Depends(get_db)):
    return db.query(Hashtag).all()

@router.post("/tickets/{ticket_id}")
def set_ticket_hashtags(ticket_id: int, hashtags: list[str], db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trovato")

    tags = []
    for name in hashtags:
        tag = db.query(Hashtag).filter(Hashtag.name == name).first()
        if not tag:
            tag = Hashtag(name=name)
            db.add(tag)
            db.flush()
        tags.append(tag)
    ticket.hashtags = tags
    db.commit()
    return {"hashtags": [t.name for t in tags]}

@router.post("/tasks/{task_id}")
def set_task_hashtags(task_id: int, hashtags: list[str], db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task non trovato")

    tags = []
    for name in hashtags:
        tag = db.query(Hashtag).filter(Hashtag.name == name).first()
        if not tag:
            tag = Hashtag(name=name)
            db.add(tag)
            db.flush()
        tags.append(tag)
    task.hashtags = tags
    db.commit()
    return {"hashtags": [t.name for t in tags]}
