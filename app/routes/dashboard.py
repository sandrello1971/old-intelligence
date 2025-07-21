# dashboard.py – Visualizzazione HTML delle attività

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.activity import Activity

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard/activities", response_class=HTMLResponse)
def dashboard_activities(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Mostra una tabella HTML con tutte le attività presenti nel database.
    Utile per operatori, consulenti e debugging manuale.
    """
    activities = db.query(Activity).order_by(Activity.created_at.desc()).all()
    return templates.TemplateResponse("activities_dashboard.html", {
        "request": request,
        "activities": activities
    })

@router.get("/dashboard", response_class=HTMLResponse)
def show_dashboard(request: Request, db: Session = Depends(get_db)):
    activities = db.query(Activity).all()
    return templates.TemplateResponse("activities_dashboard.html", {
        "request": request,
        "activities": activities
    })


