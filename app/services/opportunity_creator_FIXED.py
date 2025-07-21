# Copia tutto da opportunity_creator.py TRANNE la sezione ticket = Ticket(...)
# Sostituisci la sezione con questa versione corretta:

            # 🔄 FIX: Usa owner dinamico e account I24
            # Trova account I24 per questo customer
            i24_ticket = db_session.query(Ticket).filter(
                Ticket.ticket_code.like("TCK-I24%"),
                Ticket.customer_name == company.nome
            ).first()
            
            i24_account = i24_ticket.account if i24_ticket else opportunity.proprietario
            
            # Trova nome owner dall'ID
            from app.models.user import User
            owner_user = db_session.query(User).filter(User.id == str(actual_owner)).first()
            owner_name = f"{owner_user.name} {owner_user.surname}".strip() if owner_user else "Owner Sconosciuto"
            
            ticket = Ticket(
                activity_id=activity.id,
                ticket_code=ticket_code,
                title=f"{milestone.name} - {ticket_code}",
                description="Creato da Fase CRM",
                customer_name=company.nome,
                priority=2,
                status=0,
                owner=owner_name,
                owner_id=str(actual_owner),
                account=i24_account,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                due_date=datetime.utcnow() + timedelta(days=5)
            )
