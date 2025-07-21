from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.models.activity import Activity
from app.models.ticket import Ticket
from app.models.task import Task
from app.models.milestone import Milestone
from app.schemas.activity_m24 import ActivityTreeM24Schema

router = APIRouter(prefix="/api/activities/tree/m24")

def build_task_tree(tasks: list[Task]) -> list[dict]:
    id_map = {t.id: {"task": t, "children": []} for t in tasks}
    for t in tasks:
        if t.predecessor_id and t.predecessor_id in id_map:
            id_map[t.predecessor_id]["children"].append(id_map[t.id])
    roots = [n for n in id_map.values() if not n["task"].predecessor_id or n["task"].predecessor_id not in id_map]
    return [serialize_task_with_children(n["task"], n["children"]) for n in roots]

def serialize_task_with_children(task: Task, children: list[dict]) -> dict:
    return {
        "id": task.id,
        "title": task.title or "",
        "status": str(task.status or "aperto"),
        "priority": str(task.priority or "bassa"),
        "children": [serialize_task_with_children(c["task"], c["children"]) for c in children]
    }

def serialize_milestone(milestone: Milestone, tasks: list[Task]) -> dict:
    all_tasks_closed = all(t.status == "chiuso" for t in tasks)
    return {
        "id": milestone.id,
        "title": f"{milestone.name} - Milestone",
        "type": "milestone",
        "status": "closed" if all_tasks_closed else "open",
        "priority": "1",
        "gtd_type": "",
        "tasks": [],
        "children": build_task_tree(tasks)
    }



def serialize_ticket(ticket: Ticket, all_tickets: list, milestones_by_ticket: dict) -> dict:
    children = [serialize_ticket(t, all_tickets, milestones_by_ticket) for t in all_tickets if t.parent_id == ticket.id]
    milestones = milestones_by_ticket.get(ticket.id, {})
    milestone_nodes = [serialize_milestone(m, tasks) for m, tasks in milestones.items()]
    return {
        "id": ticket.id,
        "ticket_code": ticket.ticket_code or "",
        "title": f"{ticket.ticket_code or ''} - {ticket.title or ''}",
        "status": str(ticket.status or "open"),
        "priority": str(ticket.priority or "2"),
        "type": "ticket",
        "gtd_type": "",
        "tasks": [],
        "children": milestone_nodes + children,
    }

@router.get("", response_model=List[ActivityTreeM24Schema])
def get_m24_activity_tree(db: Session = Depends(get_db)):
    activities = db.query(Activity).filter(Activity.activity_type.ilike("%Ulisse%"))\
        .options(
            joinedload(Activity.tickets).joinedload(Ticket.tasks).joinedload(Task.milestone)
        ).all()

    all_tickets = db.query(Ticket).all()
    all_tasks = db.query(Task).all()

    milestones_by_ticket = {}
    for task in all_tasks:
        if task.ticket_id and task.milestone:
            milestones_by_ticket.setdefault(task.ticket_id, {}).setdefault(task.milestone, []).append(task)

    response = []
    for activity in activities:
        root_tickets = [t for t in activity.tickets if t.parent_id is None]
        serialized_tickets = [serialize_ticket(t, all_tickets, milestones_by_ticket) for t in root_tickets]
        is_closed = all(t.status == 1 for t in activity.tickets)
        response.append({
            "id": activity.id,
            "description": f"{activity.id} - {(activity.customer_name or '').strip() or '(senza azienda)'}",
            "status": "closed" if is_closed else "open",
            "tickets": serialized_tickets,
            "customer_name": activity.customer_name
        })
    return response
