from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.ticket import Ticket
from app.models.task import Task
from app.models.activity import Activity
from app.models.opportunity import Opportunity
from app.routes.ticket_generator import SERVICE_LABELS


def get_opportunities_progress_data(db: Session):
    output = {
        "incarichi_24": {
            "totale": 0,
            "fasi_totali": 0,
            "fasi_concluse": 0
        },
        "opportunita": []
    }

    # --- INCARICHI 24 MESI ---
    incarichi = db.query(Ticket).filter(Ticket.ticket_code.like("TCK-I24%")).all()
    output["incarichi_24"]["totale"] = len(incarichi)
    for t in incarichi:
        output["incarichi_24"]["fasi_totali"] += len(t.tasks)
        output["incarichi_24"]["fasi_concluse"] += sum(1 for task in t.tasks if task.status == "chiuso")

    # --- OPPORTUNITA ---
    opportunities = db.query(Opportunity).all()
    servizio_map = {}

    for opp in opportunities:
        label = SERVICE_LABELS.get(opp.codice[:3], opp.codice)
        if label not in servizio_map:
            servizio_map[label] = {
                "servizio": label,
                "ticket_count": 0,
                "dettagli": []
            }

        tickets = db.query(Ticket).filter(Ticket.ticket_code.like(f"TCK-{opp.codice[:3]}%"), Ticket.customer_name == opp.cliente).all()
        servizio_map[label]["ticket_count"] += len(tickets)

        for t in tickets:
            tasks = db.query(Task).filter(Task.ticket_id == t.id).all()
            servizio_map[label]["dettagli"].append({
                "ticket": t.ticket_code,
                "fasi_totali": len(tasks),
                "fasi_concluse": sum(1 for task in tasks if task.status == "chiuso"),
                "fasi": [{"title": task.title, "status": task.status} for task in tasks]
            })

    output["opportunita"] = list(servizio_map.values())
    return output
