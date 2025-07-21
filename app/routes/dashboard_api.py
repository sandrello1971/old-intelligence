from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.ticket import Ticket
from app.models.task import Task
from app.models.opportunity import Opportunity
from app.models.activity import Activity

router = APIRouter(tags=["dashboard"])  # <-- rimosso il prefisso duplicato

@router.get("/dashboard/opportunities/progress_v2")
def get_opportunities_progress_data(db: Session = Depends(get_db)):
    # Commesse 24 mesi
    incarichi = db.query(Ticket).filter(Ticket.ticket_code.like("TCK-I24%"), Ticket.tasks.any()).all()
    fasi_totali = 0
    fasi_concluse = 0
    for t in incarichi:
        fasi_totali += len(t.tasks)
        fasi_concluse += len([task for task in t.tasks if task.status == "chiuso"])

    incarichi_data = {
        "totale": len(incarichi),
        "fasi_totali": fasi_totali,
        "fasi_concluse": fasi_concluse,
    }

    # Opportunità per servizio
    results = []
    tickets = db.query(Ticket).filter(Ticket.ticket_code.notlike("TCK-I24%"), Ticket.tasks.any()).all()

    # Raggruppa i ticket per servizio (fallback: opportunità.titolo)
    service_map = {}
    for ticket in tickets:
        servizi = ticket.detected_services or []

        # Fallback: se vuoto prova a usare il nome opportunità
        if not servizi and hasattr(ticket, 'opportunity') and ticket.opportunity:
            titolo = ticket.opportunity.titolo
            if "[" in titolo and "]" in titolo:
                fallback_servizio = titolo.split("[")[1].split("]")[0].strip()
                servizi = [fallback_servizio]

        for svc in servizi:
            service_map.setdefault(svc, []).append(ticket)

    for service, service_tickets in service_map.items():
        dettagli = []
        for ticket in service_tickets:
            fasi = [
                {
                    "title": t.title,
                    "status": t.status
                } for t in ticket.tasks
            ]
            dettagli.append({
                "ticket": ticket.ticket_code,
                "fasi_totali": len(ticket.tasks),
                "fasi_concluse": len([t for t in ticket.tasks if t.status == "chiuso"]),
                "fasi": fasi
            })

        results.append({
            "servizio": service,
            "ticket_count": len(service_tickets),
            "dettagli": dettagli
        })

    return {
        "incarichi_24": incarichi_data,
        "opportunita": results
    }


@router.get("/dashboard/opportunities/by_service")
def get_opportunity_by_service_aggregated(db: Session = Depends(get_db)):
    tickets = db.query(Ticket).filter(Ticket.ticket_code.notlike("TCK-I24%"), Ticket.tasks.any()).all()

    service_counts = {}
    for ticket in tickets:
        servizi = ticket.detected_services or []

        if not servizi and hasattr(ticket, 'opportunity') and ticket.opportunity:
            titolo = ticket.opportunity.titolo
            if "[" in titolo and "]" in titolo:
                fallback_servizio = titolo.split("[")[1].split("]")[0].strip()
                servizi = [fallback_servizio]

        for svc in servizi:
            if svc not in service_counts:
                service_counts[svc] = {"aperto": 0, "in_corso": 0, "chiuso": 0}

            for t in ticket.tasks:
                service_counts[svc][t.status] = service_counts[svc].get(t.status, 0) + 1

    return service_counts
