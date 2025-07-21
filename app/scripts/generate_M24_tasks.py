import os
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from app.models.ticket import Ticket
from app.models.task import Task
from app.models.milestone import Milestone
from app.models.phase_template import PhaseTemplate

# ========== CONFIG ==========
load_dotenv("/app/.env")

DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{DB_HOST}:5432/{os.getenv('POSTGRES_DB')}"

# ========== DB SETUP ==========
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

# ========== FUNZIONE ==========
def generate_m24_tasks():
    print("\n🚀 Avvio generazione task per ticket M24...")

    milestone = session.query(Milestone).filter_by(name="Firma M24").first()
    if not milestone:
        print("❌ Milestone 'Firma M24' non trovata. Interrompo.")
        return

    phase_templates = session.query(PhaseTemplate).filter_by(code="M24").order_by(PhaseTemplate.id).all()
    if not phase_templates:
        print("❌ Nessuna fase trovata per codice M24.")
        return

    phase_titles = [p.description for p in phase_templates]

    tickets = session.query(Ticket).filter(Ticket.ticket_code.ilike("TKC-M24-%")).all()
    created = 0

    for ticket in tickets:
        existing_tasks = session.query(Task).filter_by(ticket_id=ticket.id).count()
        if existing_tasks:
            print(f"⚠️ Task già presenti per ticket {ticket.ticket_code}, skip.")
            continue

        owner_name = ticket.owner or "AI"
        owner_id = session.execute(
            text("SELECT id FROM owners WHERE surname = :surname"),
            {"surname": owner_name.split()[-1]}  # fallback semplificato
        ).scalar()

        if not owner_id:
            print(f"⚠️ Owner '{owner_name}' non trovato per ticket {ticket.ticket_code}, uso 'AI'.")
            owner_id = session.execute(
                text("SELECT id FROM owners WHERE surname = 'AI'")
            ).scalar()

        previous_task = None
        for phase_title in phase_titles:
            task = Task(
                ticket_id=ticket.id,
                title=f"{ticket.ticket_code} - {phase_title}",
                description=f"Fase '{phase_title}' per il progetto Ulisse.",
                priority="bassa",
                status="aperto",
                milestone_id=milestone.id,
                owner=owner_id,
                predecessor_id=previous_task.id if previous_task else None
            )
            session.add(task)
            session.commit()
            previous_task = task

        print(f"✅ Task creati per ticket {ticket.ticket_code}")
        created += 1

    print(f"\n📅 Completato: task generati per {created} ticket M24.")

# ========== MAIN ==========
if __name__ == "__main__":
    generate_m24_tasks()
