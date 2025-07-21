from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from sqlalchemy import text
from typing import List

router = APIRouter(prefix="/sub-types", tags=["Services"])

@router.get("/")
async def get_sub_types(db: Session = Depends(get_db)):
    """Ottieni tutti i servizi"""
    try:
        result = db.execute(text("SELECT id, name, code, description FROM sub_types ORDER BY code"))
        services = []
        for row in result:
            services.append({
                "id": row.id,
                "name": row.name, 
                "code": row.code,
                "description": row.description or ""
            })
        return services
    except Exception as e:
        raise HTTPException(500, f"Errore database: {str(e)}")

@router.post("/")
async def create_sub_type(data: dict, db: Session = Depends(get_db)):
    """Crea nuovo servizio"""
    if not data.get("name") or not data.get("code"):
        raise HTTPException(400, "Nome e codice obbligatori")
    
    code = data["code"].upper()
    
    try:
        # Verifica codice univoco
        existing = db.execute(text("SELECT id FROM sub_types WHERE code = :code"), {"code": code}).first()
        if existing:
            raise HTTPException(400, f"Codice {code} già esistente")
        
        # Inserimento
        db.execute(text("""
            INSERT INTO sub_types (name, code, description) 
            VALUES (:name, :code, :description)
        """), {
            "name": data["name"],
            "code": code,
            "description": data.get("description", "")
        })
        db.commit()
        
        # Recupera il nuovo record
        new_service = db.execute(text("SELECT id, name, code FROM sub_types WHERE code = :code"), {"code": code}).first()
        
        return {"id": new_service.id, "name": new_service.name, "code": new_service.code}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Errore creazione servizio: {str(e)}")

@router.patch("/{service_id}")
async def update_sub_type(service_id: int, data: dict, db: Session = Depends(get_db)):
    """Aggiorna servizio"""
    try:
        # Verifica esistenza
        existing = db.execute(text("SELECT id FROM sub_types WHERE id = :id"), {"id": service_id}).first()
        if not existing:
            raise HTTPException(404, "Servizio non trovato")
        
        # Costruisce query dinamica
        updates = []
        params = {"id": service_id}
        
        if "name" in data:
            updates.append("name = :name")
            params["name"] = data["name"]
        if "code" in data:
            updates.append("code = :code")
            params["code"] = data["code"].upper()
        if "description" in data:
            updates.append("description = :description")
            params["description"] = data["description"]
        
        if updates:
            query = f"UPDATE sub_types SET {', '.join(updates)} WHERE id = :id"
            db.execute(text(query), params)
            db.commit()
        
        # Ritorna aggiornato
        updated = db.execute(text("SELECT id, name, code FROM sub_types WHERE id = :id"), {"id": service_id}).first()
        return {"id": updated.id, "name": updated.name, "code": updated.code}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Errore aggiornamento: {str(e)}")

@router.delete("/{service_id}")
async def delete_sub_type(service_id: int, db: Session = Depends(get_db)):
    """Elimina servizio"""
    try:
        # Verifica esistenza
        existing = db.execute(text("SELECT id FROM sub_types WHERE id = :id"), {"id": service_id}).first()
        if not existing:
            raise HTTPException(404, "Servizio non trovato")
        
        # Verifica dipendenze
        activities_count = db.execute(text("SELECT COUNT(*) as count FROM activities WHERE sub_type_id = :id"), {"id": service_id}).first()
        if activities_count.count > 0:
            raise HTTPException(400, f"Impossibile eliminare: {activities_count.count} attività associate")
        
        # Elimina
        db.execute(text("DELETE FROM sub_types WHERE id = :id"), {"id": service_id})
        db.commit()
        
        return {"message": "Servizio eliminato con successo"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Errore eliminazione: {str(e)}")

@router.get("/{service_id}/stats")
async def get_service_stats(service_id: int, db: Session = Depends(get_db)):
    """Statistiche per servizio"""
    try:
        stats = db.execute(text("""
            SELECT 
                COUNT(DISTINCT a.id) as activities_count,
                COUNT(DISTINCT m.id) as milestones_count,
                COUNT(DISTINCT t.id) as tasks_count
            FROM sub_types st
            LEFT JOIN activities a ON a.sub_type_id = st.id
            LEFT JOIN milestones m ON m.project_type = st.code
            LEFT JOIN tasks t ON t.milestone_id = m.id
            WHERE st.id = :id
        """), {"id": service_id}).first()
        
        if not stats:
            raise HTTPException(404, "Servizio non trovato")
        
        return {
            "service_id": service_id,
            "activities_count": stats.activities_count or 0,
            "milestones_count": stats.milestones_count or 0,
            "tasks_count": stats.tasks_count or 0
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Errore statistiche: {str(e)}")
