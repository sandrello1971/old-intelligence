from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from sqlalchemy import text
from typing import List

router = APIRouter(prefix="/service-user-associations", tags=["Service Users"])

@router.get("/")
async def get_associations(db: Session = Depends(get_db)):
    """Ottieni tutte le associazioni"""
    try:
        result = db.execute(text("""
            SELECT 
                sua.id,
                sua.service_id,
                sua.user_id,
                sua.role,
                st.code as service_code,
                st.name as service_name,
                u.name as user_name,
                u.surname as user_surname
            FROM service_user_associations sua
            JOIN sub_types st ON sua.service_id = st.id
            LEFT JOIN users u ON sua.user_id = u.id
            ORDER BY st.code, u.name
        """))
        
        associations = []
        for row in result:
            associations.append({
                "id": row.id,
                "service_id": row.service_id,
                "user_id": row.user_id,
                "role": row.role,
                "service_code": row.service_code,
                "service_name": row.service_name,
                "user_name": f"{row.user_name or ''} {row.user_surname or ''}".strip()
            })
        
        return associations
    except Exception as e:
        raise HTTPException(500, f"Errore recupero associazioni: {str(e)}")

@router.post("/")
async def create_association(data: dict, db: Session = Depends(get_db)):
    """Crea nuova associazione"""
    if not data.get("service_id") or not data.get("user_id"):
        raise HTTPException(400, "Service ID e User ID obbligatori")
    
    try:
        # Verifica se esiste già
        existing = db.execute(text("""
            SELECT id FROM service_user_associations 
            WHERE service_id = :service_id AND user_id = :user_id
        """), {
            "service_id": data["service_id"],
            "user_id": data["user_id"]
        }).first()
        
        if existing:
            raise HTTPException(400, "Associazione già esistente")
        
        # Inserisci
        db.execute(text("""
            INSERT INTO service_user_associations (service_id, user_id, role)
            VALUES (:service_id, :user_id, :role)
        """), {
            "service_id": data["service_id"],
            "user_id": data["user_id"],
            "role": data.get("role", "responsible")
        })
        db.commit()
        
        return {"message": "Associazione creata con successo"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Errore creazione associazione: {str(e)}")

@router.delete("/{association_id}")
async def delete_association(association_id: int, db: Session = Depends(get_db)):
    """Elimina associazione"""
    try:
        result = db.execute(text("DELETE FROM service_user_associations WHERE id = :id"), {"id": association_id})
        
        if result.rowcount == 0:
            raise HTTPException(404, "Associazione non trovata")
        
        db.commit()
        return {"message": "Associazione eliminata"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Errore eliminazione: {str(e)}")

@router.get("/matrix")
async def get_association_matrix(db: Session = Depends(get_db)):
    """Matrice servizi-utenti per interfaccia"""
    try:
        # Ottieni tutti i servizi
        services = db.execute(text("SELECT id, code, name FROM sub_types ORDER BY code")).fetchall()
        
        # Ottieni tutti gli utenti
        users = db.execute(text("SELECT id, name, surname FROM users ORDER BY name")).fetchall()
        
        # Ottieni associazioni esistenti
        associations = db.execute(text("""
            SELECT service_id, user_id 
            FROM service_user_associations
        """)).fetchall()
        
        # Crea matrice
        association_map = {f"{a.service_id},{a.user_id}": True for a in associations}
        
        matrix = {
            "services": [{"id": s.id, "code": s.code, "name": s.name} for s in services],
            "users": [{"id": u.id, "name": u.name, "surname": u.surname} for u in users],
            "associations": association_map
        }
        
        return matrix
    except Exception as e:
        raise HTTPException(500, f"Errore matrice: {str(e)}")
