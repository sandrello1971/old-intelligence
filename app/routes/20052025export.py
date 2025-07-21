from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from io import StringIO
from datetime import datetime
from app.core.database import get_db
from app.models.ticket import Ticket
from app.models.task import Task

router = APIRouter(prefix="/export", tags=["export"])

@router.get("/tasks/obsidian")
def export_tasks_obsidian(db: Session = Depends(get_db)):
    buffer = StringIO()
    today = datetime.utcnow().strftime("%Y-%m-%d")

    # Recupera tutti i ticket con i task associati
    tickets = db.query(Ticket).options(
        joinedload(Ticket.tasks),
        joinedload(Ticket.milestone)
    ).all()

    already_written = set()

    for ticket in tickets:
        if ticket.id in already_written:
            continue
        already_written.add(ticket.id)

        company = ticket.customer_name or "Azienda Sconosciuta"
        milestone_name = ticket.title or "Milestone"
        code = ticket.ticket_code or "SenzaCodice"
        due_date = ticket.due_date.date().isoformat() if ticket.due_date else today
        owner_full = ticket.owner or "Anonimo"
        owner_tag = f"#{owner_full.replace(' ', '')}"

        # Riga principale del ticket
        line = f"- [ ] {company} - {milestone_name} - {owner_tag} 🔼 📅 {due_date}\n"
        buffer.write(line)

        for task in ticket.tasks:
            task_title = task.title or "Task senza titolo"
            task_prefix = "[x]" if task.status == "chiuso" else "[ ]"
            buffer.write(f"\t- {task_prefix} {task_title}\n")

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="text/markdown",
        headers={"Content-Disposition": "attachment; filename=Ticketing_Tasks.md"}
    )
