from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from io import StringIO
from datetime import datetime
from app.core.database import get_db
from app.models.ticket import Ticket
from app.models.task import Task
import re

router = APIRouter(prefix="/export", tags=["export"])

@router.get("/tasks/obsidian")
def export_tasks_obsidian(db: Session = Depends(get_db)):
    buffer = StringIO()
    today = datetime.utcnow().strftime("%Y-%m-%d")

    tickets = db.query(Ticket).options(
        joinedload(Ticket.tasks),
        joinedload(Ticket.milestone)
    ).all()

    written_ticket_ids = set()

    for ticket in tickets:
        if ticket.id in written_ticket_ids:
            continue
        written_ticket_ids.add(ticket.id)

        company = ticket.customer_name or "Azienda Sconosciuta"
        milestone_title = ticket.title or "Milestone"
        code = ticket.ticket_code or "SenzaCodice"
        due_date = ticket.due_date.date().isoformat() if ticket.due_date else today
        owner_tag = f"#{(ticket.owner or 'Anonimo').replace(' ', '')}"
        
        # Sanifica la descrizione eliminando newline, markdown break e tag fuori posto
        raw_descr = ticket.description or "Nessuna descrizione"
        descrizione = re.sub(r'[\n\r]+', ' ', raw_descr).strip()
        descrizione = re.sub(r'-{3,}', '', descrizione)

        # Codice opportunità (es: I24, F40, PBX)
        opportunity_code = code.replace("TCK-", "").split("-")[0]
        tags = [f"#{opportunity_code}", "#Ticket"]

        buffer.write(
            f"- [ ] {company} - {milestone_title} - Descrizione: {descrizione} - {owner_tag} {' '.join(tags)} 🔼 📅 {due_date}\n"
        )

        for task in ticket.tasks:
            status_prefix = "[x]" if task.status == "chiuso" else "[ ]"
            task_title = task.title or "Task senza titolo"
            task_descr = re.sub(r'[\n\r]+', ' ', task.description or task_title).strip()
            task_descr = re.sub(r'-{3,}', '', task_descr)
            buffer.write(f"\t- {status_prefix} {task_title} - Descrizione: {task_descr} #Task\n")

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="text/markdown",
        headers={"Content-Disposition": "attachment; filename=Ticketing_Tasks.md"}
    )
