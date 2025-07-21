from datetime import datetime
from integrations.crm_incloud.activity import update_crm_activity

def update_crm_ticket_description(ticket, task):
    from datetime import datetime

    try:
        activity = ticket.activity
        if not activity:
            print("⚠️ Nessuna attività associata al ticket.")
            return

        now = datetime.utcnow().isoformat() + "Z"
        note = f"✅ Il task \"{task.title}\" è stato chiuso — {now}"

        payload = {
            "id": activity.id,
            "description": note
        }

        update_crm_activity(payload)
        print(f"🟢 CRM aggiornato con: {note}")

    except Exception as e:
        print(f"❌ Errore aggiornamento CRM: {e}")
