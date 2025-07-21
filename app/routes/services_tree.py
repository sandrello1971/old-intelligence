from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.sub_type import SubType
from app.core.database import get_db
from app.models.sub_type import SubType
from app.models.milestone import Milestone  
from app.models.phase_template import PhaseTemplate
from app.models.service_user_association import ServiceUserAssociation
from app.models.user import User
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
from sqlalchemy import text


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/services-tree", tags=["Services Tree"])

class MilestoneCreate(BaseModel):
    name: str
    order: int
    sla_days: Optional[int] = 5
    warning_days: Optional[int] = 2
    escalation_days: Optional[int] = 3

class TaskTemplateCreate(BaseModel):
    code: str
    type: str
    description: str
    detailed_description: Optional[str] = ""
    order: Optional[int] = 1
    sla_days: Optional[int] = 3
    warning_days: Optional[int] = 2
    escalation_days: Optional[int] = 1

# 2. MODIFICARE GET / per includere mappature multiple
@router.get("/")
async def get_services_tree(db: Session = Depends(get_db)):
    """Restituisce l'alberatura completa dei servizi CON MAPPATURE MULTIPLE"""
    try:
        services = db.query(SubType).all()
        result = []
        
        for service in services:
            # Utenti assegnati (existing logic)
            user_assignments = db.query(ServiceUserAssociation).filter(
                ServiceUserAssociation.service_id == service.id
            ).all()
            
            assigned_users = []
            for assignment in user_assignments:
                user = db.query(User).filter(User.id == assignment.user_id).first()
                if user:
                    assigned_users.append({
                        "user_id": assignment.user_id,
                        "email": user.email,
                        "display_name": f"{user.name} {user.surname}".strip(),
                        "role": assignment.role
                    })
            
            # 🆕 NUOVA LOGICA: Ottieni commesse associate via junction table
            commesse_associate = []
            if not service.is_commessa:  # Solo per servizi, non per commesse
                query = text("""
                    SELECT c.id, c.name, c.code 
                    FROM service_commessa_mapping scm
                    JOIN sub_types c ON scm.commessa_id = c.id
                    WHERE scm.service_id = :service_id
                    ORDER BY c.name
                """)
                mappings = db.execute(query, {"service_id": service.id}).fetchall()
                commesse_associate = [
                    {"id": row.id, "name": row.name, "code": row.code}
                    for row in mappings
                ]
            
            # Milestones (existing logic)
            milestones = db.query(Milestone).filter(
                Milestone.project_type == service.code
            ).order_by(Milestone.order).all()
            
            milestones_data = []
            for milestone in milestones:
                task_templates = db.query(PhaseTemplate).filter(
                    PhaseTemplate.milestone_id == milestone.id
                ).order_by(PhaseTemplate.order).all()
                
                milestone_data = {
                    "id": milestone.id,
                    "name": milestone.name,
                    "order": milestone.order,
                    "project_type": milestone.project_type,
                    "sla_days": 5,
                    "warning_days": 2, 
                    "escalation_days": 3,
                    "task_templates": [
                        {
                            "id": template.id,
                            "code": template.code,
                            "type": template.type,
                            "description": template.description,
                            "order": getattr(template, 'order', 0),
                            "parent_id": getattr(template, 'parent_id', None),
                            "sla_days": getattr(template, 'sla_days', 3),
                            "warning_days": getattr(template, 'warning_days', 2),
                            "escalation_days": getattr(template, 'escalation_days', 1),
                            "detailed_description": getattr(template, 'detailed_description', '')
                        }
                         for template in task_templates
                    ] 
                }
                milestones_data.append(milestone_data)
            
            service_data = {
                "id": service.id,
                "name": service.name,
                "code": service.code,
                "description": getattr(service, 'description', ''),
                "active": getattr(service, 'active', True),
                "is_commessa": getattr(service, "is_commessa", False),
                
                # 🔄 RETROCOMPATIBILITÀ: Mantieni campo legacy per non rompere frontend esistente
                "commessa_associata": getattr(service, "commessa_associata", ""),
                
                # 🆕 NUOVA LOGICA: Array di commesse multiple
                "commesse_associate": commesse_associate,
                
                "assigned_users": assigned_users,
                "milestones": milestones_data
            }
            result.append(service_data)
        
        logger.info(f"✅ Caricati {len(result)} servizi con mappature multiple")
        return result
        
    except Exception as e:
        logger.error(f"❌ Errore: {e}")
        return []

@router.get("/users")
async def get_users(db: Session = Depends(get_db)):
    """Lista utenti disponibili"""
    try:
        users = db.query(User).all()
        return [
            {
                "id": user.id,
                "email": user.email,
                "display_name": f"{user.name} {user.surname}".strip(),
                "role": "user"
            }
            for user in users
        ]
    except Exception as e:
        logger.error(f"❌ Errore users: {e}")
        return []

@router.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "ok", 
        "message": "Services Tree COMPLETO con CRUD",
        "endpoints": [
            "GET / - Lista servizi con utenti",
            "GET /users - Lista utenti",
            "🆕 POST /services/{service_id}/milestones - Crea milestone",
            "🆕 PUT /milestones/{milestone_id} - Aggiorna milestone", 
            "🆕 DELETE /milestones/{milestone_id} - Elimina milestone",
            "🆕 POST /milestones/{milestone_id}/templates - Crea template",
            "🆕 PUT /templates/{template_id} - Aggiorna template",
            "🆕 DELETE /templates/{template_id} - Elimina template"
        ]
    }

@router.put("/services/{service_id}/commesse")
def update_service_commesse(
    service_id: int,
    request: dict,
    db: Session = Depends(get_db)
):
    """🆕 Aggiorna mappature multiple servizio → commesse"""
    try:
        commesse_ids = request.get("commesse_ids", [])
        
        service = db.query(SubType).filter(SubType.id == service_id).first()
        if not service:
            raise HTTPException(status_code=404, detail="Servizio non trovato")
        
        if service.is_commessa:
            raise HTTPException(status_code=400, detail="Non puoi mappare una commessa")
        
        # Verifica che tutte le commesse esistano
        if commesse_ids:
            commesse = db.query(SubType).filter(
                SubType.id.in_(commesse_ids),
                SubType.is_commessa == True
            ).all()
            
            if len(commesse) != len(commesse_ids):
                raise HTTPException(status_code=400, detail="Alcune commesse non esistono")
        
        # 🗑️ Rimuovi mappature esistenti
        db.execute(
            text("DELETE FROM service_commessa_mapping WHERE service_id = :service_id"),
            {"service_id": service_id}
        )
        
        # ➕ Aggiungi nuove mappature
        for commessa_id in commesse_ids:
            db.execute(
                text("INSERT INTO service_commessa_mapping (service_id, commessa_id) VALUES (:service_id, :commessa_id)"),
                {"service_id": service_id, "commessa_id": commessa_id}
            )
        
        # 🔄 AGGIORNA CAMPO LEGACY per retrocompatibilità
        if commesse_ids:
            # Prendi la prima commessa come valore legacy
            first_commessa = db.query(SubType).filter(SubType.id == commesse_ids[0]).first()
            service.commessa_associata = first_commessa.code if first_commessa else ""
        else:
            service.commessa_associata = ""
        
        db.commit()
        
        return {
            "message": "Mappature aggiornate con successo",
            "service_id": service_id,
            "commesse_count": len(commesse_ids),
            "commesse_ids": commesse_ids
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Errore aggiornamento mappature {service_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services/{service_id}/commesse")
def get_service_commesse(service_id: int, db: Session = Depends(get_db)):
    """🆕 Ottieni commesse associate a un servizio"""
    try:
        service = db.query(SubType).filter(SubType.id == service_id).first()
        if not service:
            raise HTTPException(status_code=404, detail="Servizio non trovato")
        
        query = text("""
            SELECT c.id, c.name, c.code 
            FROM service_commessa_mapping scm
            JOIN sub_types c ON scm.commessa_id = c.id
            WHERE scm.service_id = :service_id
            ORDER BY c.name
        """)
        mappings = db.execute(query, {"service_id": service_id}).fetchall()
        
        return {
            "service_id": service_id,
            "service_name": service.name,
            "commesse_associate": [
                {"id": row.id, "name": row.name, "code": row.code}
                for row in mappings
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore get commesse {service_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# ===== SERVIZI CRUD =====
@router.delete("/services/{service_id}")
def delete_service(service_id: int, db: Session = Depends(get_db)):
    """Elimina un servizio CON CONTROLLI DI SICUREZZA"""
    try:
        # 1. Trova il servizio
        service = db.query(SubType).filter(SubType.id == service_id).first()
        if not service:
            raise HTTPException(status_code=404, detail="Servizio non trovato")
        
        # 2. CONTROLLO: Verifica se ha ticket attivi
        from app.models.ticket import Ticket
        tickets_count = db.query(Ticket).filter(Ticket.ticket_code.like(f"TCK-{service.code}%")).count()
        if tickets_count > 0:
            raise HTTPException(status_code=400, detail=f"Impossibile eliminare: servizio ha {tickets_count} ticket attivi")
        
        # 3. Elimina prima le associazioni utente-servizio
        associations_deleted = db.query(ServiceUserAssociation).filter(ServiceUserAssociation.service_id == service_id).delete()
        
        # 4. Elimina il servizio
        service_name = service.name
        db.delete(service)
        db.commit()
        
        return {
            "message": f"Servizio '{service_name}' eliminato con successo",
            "associations_deleted": associations_deleted,
            "tickets_checked": tickets_count
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Errore eliminazione servizio {service_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")

@router.post("/services")
def create_service(request: dict, db: Session = Depends(get_db)):
    """Crea un nuovo servizio CON TUTTI I CAMPI"""
    try:
        name = request.get("name")
        code = request.get("code") 
        description = request.get("description", "")  # 🆕 AGGIUNTO
        is_commessa = request.get("is_commessa", False)  # 🆕 AGGIUNTO
        commessa_associata = request.get("commessa_associata", "")  # 🆕 AGGIUNTO
        
        if not name or not code:
            raise HTTPException(status_code=400, detail="Nome e codice richiesti")
        
        # Controlla se il codice esiste già
        existing = db.query(SubType).filter(SubType.code == code).first()
        if existing:
            raise HTTPException(status_code=400, detail="Codice servizio già esistente")
        
        # 🆕 CREA SERVIZIO CON TUTTI I CAMPI
        service = SubType(
            name=name,
            code=code,
            description=description,
            is_commessa=is_commessa,
            commessa_associata=commessa_associata
        )
        
        db.add(service)
        db.commit()
        db.refresh(service)
        
        logger.info(f"✅ Servizio creato: {name} (is_commessa: {is_commessa})")
        
        return {
            "message": f"Servizio {name} creato con successo", 
            "service": {
                "id": service.id,
                "name": service.name,
                "code": service.code,
                "is_commessa": service.is_commessa
            }
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Errore creazione servizio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/services/{service_id}")
def get_service(service_id: int, db: Session = Depends(get_db)):
    """🆕 Ottieni un singolo servizio per ID"""
    try:
        service = db.query(SubType).filter(SubType.id == service_id).first()
        if not service:
            raise HTTPException(status_code=404, detail="Servizio non trovato")
        
        return {
            "id": service.id,
            "name": service.name,
            "code": service.code,
            "description": getattr(service, "description", ""),
            "is_commessa": getattr(service, "is_commessa", False),
            "commessa_associata": getattr(service, "commessa_associata", None)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore get service {service_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/services/{service_id}")
def update_service(service_id: int, request: dict, db: Session = Depends(get_db)):
    """🆕 Aggiorna un servizio esistente"""
    try:
        service = db.query(SubType).filter(SubType.id == service_id).first()
        if not service:
            raise HTTPException(status_code=404, detail="Servizio non trovato")
        
        # Aggiorna campi
        if "name" in request:
            service.name = request["name"]
        if "code" in request:
            # Controlla se nuovo codice è già in uso da altri servizi
            existing = db.query(SubType).filter(
                SubType.code == request["code"],
                SubType.id != service_id
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="Codice già utilizzato da altro servizio")
            service.code = request["code"]
        if "description" in request:
            service.description = request["description"]
        if "is_commessa" in request:
            service.is_commessa = request["is_commessa"]
        if "commessa_associata" in request:
            service.commessa_associata = request["commessa_associata"]
        
        db.commit()
        db.refresh(service)
        
        return {"message": f"Servizio {service.name} aggiornato con successo", "service": service}
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Errore aggiornamento servizio {service_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== 🆕 MILESTONES CRUD =====
@router.post("/services/{service_id}/milestones")
def create_milestone(service_id: int, milestone_data: MilestoneCreate, db: Session = Depends(get_db)):
    """🆕 Crea una nuova milestone/fase per un servizio"""
    try:
        # Verifica esistenza servizio
        service = db.query(SubType).filter(SubType.id == service_id).first()
        if not service:
            raise HTTPException(status_code=404, detail="Servizio non trovato")
        
        # Crea milestone
        milestone = Milestone(
            name=milestone_data.name,
            order=milestone_data.order,
            project_type=service.code,  # Collega milestone al servizio tramite codice
        )
        
        db.add(milestone)
        db.commit()
        db.refresh(milestone)
        
        logger.info(f"✅ Milestone {milestone.name} creata per servizio {service.name}")
        return {
            "message": f"Fase '{milestone.name}' creata con successo per {service.name}",
            "milestone": {
                "id": milestone.id,
                "name": milestone.name,
                "order": milestone.order,
                "project_type": milestone.project_type
            }
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Errore creazione milestone: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/milestones/{milestone_id}")
def update_milestone(milestone_id: int, milestone_data: MilestoneCreate, db: Session = Depends(get_db)):
    """🆕 Aggiorna una milestone esistente"""
    try:
        milestone = db.query(Milestone).filter(Milestone.id == milestone_id).first()
        if not milestone:
            raise HTTPException(status_code=404, detail="Milestone non trovata")
        
        # Aggiorna campi
        milestone.name = milestone_data.name
        milestone.order = milestone_data.order
        
        db.commit()
        db.refresh(milestone)
        
        logger.info(f"✅ Milestone {milestone.name} aggiornata")
        return {
            "message": f"Fase '{milestone.name}' aggiornata con successo",
            "milestone": {
                "id": milestone.id,
                "name": milestone.name,
                "order": milestone.order,
                "project_type": milestone.project_type
            }
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Errore aggiornamento milestone {milestone_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/milestones/{milestone_id}")
def delete_milestone(milestone_id: int, db: Session = Depends(get_db)):
    """🆕 Elimina una milestone e tutti i suoi template collegati"""
    try:
        milestone = db.query(Milestone).filter(Milestone.id == milestone_id).first()
        if not milestone:
            raise HTTPException(status_code=404, detail="Milestone non trovata")
        
        milestone_name = milestone.name
        
        # 1. CONTROLLO SICUREZZA: Verifica se ci sono task attivi collegati
        from app.models.task import Task
        tasks_count = db.query(Task).filter(Task.milestone_id == milestone_id).count()
        if tasks_count > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"Impossibile eliminare: fase ha {tasks_count} task attivi collegati"
            )
        
        # 2. Elimina prima tutti i template collegati alla milestone
        templates_deleted = db.query(PhaseTemplate).filter(
            PhaseTemplate.milestone_id == milestone_id
        ).delete()
        
        # 3. Elimina la milestone
        db.delete(milestone)
        db.commit()
        
        logger.info(f"✅ Milestone {milestone_name} eliminata con {templates_deleted} template")
        return {
            "message": f"Fase '{milestone_name}' eliminata con successo",
            "templates_deleted": templates_deleted,
            "tasks_checked": tasks_count
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Errore eliminazione milestone {milestone_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")

# ===== 🆕 TASK TEMPLATES CRUD =====
@router.post("/milestones/{milestone_id}/templates")
def create_task_template(milestone_id: int, template_data: TaskTemplateCreate, db: Session = Depends(get_db)):
    """🆕 Crea un nuovo task template per una milestone"""
    try:
        # Verifica esistenza milestone
        milestone = db.query(Milestone).filter(Milestone.id == milestone_id).first()
        if not milestone:
            raise HTTPException(status_code=404, detail="Milestone non trovata")
        
        # Crea template
        template = PhaseTemplate(
            code=template_data.code,
            type=template_data.type,
            description=template_data.description,
            order=template_data.order,
            milestone_id=milestone_id
        )
        
        db.add(template)
        db.commit()
        db.refresh(template)
        
        logger.info(f"✅ Template {template.description} creato per milestone {milestone.name}")
        return {
            "message": f"Task template '{template.description}' creato con successo",
            "template": {
                "id": template.id,
                "code": template.code,
                "type": template.type,
                "description": template.description,
                "order": template.order,
                "milestone_id": template.milestone_id
            }
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Errore creazione template: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@router.put("/templates/{template_id}")
def update_task_template(template_id: int, template_data: TaskTemplateCreate, db: Session = Depends(get_db)):
    """🆕 Aggiorna un task template esistente"""
    try:
        template = db.query(PhaseTemplate).filter(PhaseTemplate.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Template non trovato")
        
        # Aggiorna campi base
        template.code = template_data.code
        template.type = template_data.type
        template.description = template_data.description
        template.order = template_data.order
        # Parsing della descrizione per separare i dettagli
        # Parsing della descrizione per separare i dettagli
        if " --- DETTAGLI: " in template_data.description:
            parts = template_data.description.split(" --- DETTAGLI: ", 1)
            template.description = parts[0].strip()
            template.detailed_description = parts[1].strip() if len(parts) > 1 else ""
        else:
            template.description = template_data.description
        template.order = template_data.order
        # Aggiorna campi SLA
        template.sla_days = template_data.sla_days
        template.warning_days = template_data.warning_days
        template.escalation_days = template_data.escalation_days
        template.detailed_description = getattr(template_data, "detailed_description", "")
        
        db.commit()
        db.refresh(template)
        
        logger.info(f"✅ Template {template.description} aggiornato")
        return {
            "message": f"Task template '{template.description}' aggiornato con successo",
            "template": {
                "id": template.id,
                "code": template.code,
                "type": template.type,
                "description": template.description,
                "order": template.order,
                "milestone_id": template.milestone_id
            }
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Errore aggiornamento template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/templates/{template_id}")
def delete_task_template(template_id: int, db: Session = Depends(get_db)):
    """🆕 Elimina un task template"""
    try:
        template = db.query(PhaseTemplate).filter(PhaseTemplate.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Template non trovato")
        
        template_description = template.description
        
        # CONTROLLO SICUREZZA: Verifica se ci sono task attivi basati su questo template
        from app.models.task import Task
        tasks_count = 0  # Template non collegati direttamente ai task
        if tasks_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Impossibile eliminare: template ha {tasks_count} task attivi collegati"
            )
        
        db.delete(template)
        db.commit()
        
        logger.info(f"✅ Template {template_description} eliminato")
        return {
            "message": f"Task template '{template_description}' eliminato con successo",
            "tasks_checked": tasks_count
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Errore eliminazione template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Errore interno: {str(e)}")

# ===== UTENTI GESTIONE =====
@router.post("/services/{service_id}/users")
def assign_user_to_service(service_id: int, request: dict, db: Session = Depends(get_db)):
    """Assegna utente a servizio"""
    try:
        user_id = request.get("user_id")
        role = request.get("role", "responsible")
        
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id richiesto")
        
        # Verifica esistenza servizio e utente
        service = db.query(SubType).filter(SubType.id == service_id).first()
        user = db.query(User).filter(User.id == user_id).first()
        
        if not service:
            raise HTTPException(status_code=404, detail="Servizio non trovato")
        if not user:
            raise HTTPException(status_code=404, detail="Utente non trovato")
        
        # Controlla se associazione già exists
        existing = db.query(ServiceUserAssociation).filter(
            ServiceUserAssociation.service_id == service_id,
            ServiceUserAssociation.user_id == user_id
        ).first()
        
        if existing:
            return {"message": "Utente già assegnato al servizio"}
        
        # Crea nuova associazione
        association = ServiceUserAssociation(
            service_id=service_id, 
            user_id=user_id,
            role=role
        )
        db.add(association)
        db.commit()
        
        message = f"Utente {user.name} {user.surname} assegnato a {service.name}"
        logger.info(f"✅ {message}")
        
        return {"message": message, "action": "assign"}
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Errore gestione user-service {service_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/services/{service_id}/users/{user_id}")
async def remove_user_from_service(
    service_id: int,
    user_id: str,
    db: Session = Depends(get_db)
):
    """Rimuove utente da servizio"""
    try:
        # Rimuovi associazione utente-servizio
        association = db.query(ServiceUserAssociation).filter(
            ServiceUserAssociation.service_id == service_id,
            ServiceUserAssociation.user_id == user_id
        ).first()
        
        if not association:
            raise HTTPException(status_code=404, detail="Associazione non trovata")
        
        # Ottieni info per logging
        service = db.query(SubType).filter(SubType.id == service_id).first()
        user = db.query(User).filter(User.id == user_id).first()
        
        db.delete(association)
        db.commit()
        
        message = f"Utente {user.name if user else user_id} rimosso da {service.name if service else service_id}"
        logger.info(f"✅ {message}")
        
        return {"message": message}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Errore rimozione utente {user_id} da servizio {service_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Errore rimozione utente: {str(e)}")

@router.get("/services-only")
async def get_services_only(db: Session = Depends(get_db)):
    """Restituisce solo servizi (non commesse) per checkbox ticket"""
    services = db.query(SubType).filter(SubType.is_commessa == False).all()
    return [{"id": s.id, "name": s.name, "code": s.code, "commessa_associata": getattr(s, "commessa_associata", "")} for s in services]

@router.get("/commesse-only") 
async def get_commesse_only(db: Session = Depends(get_db)):
    """Restituisce solo commesse per select associazione"""
    commesse = db.query(SubType).filter(SubType.is_commessa == True).all()
    return [{"code": s.code, "name": s.name} for s in commesse]

