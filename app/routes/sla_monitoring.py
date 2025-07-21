from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.sla_escalation_service import sla_escalation_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sla", tags=["SLA Monitoring"])

@router.get("/health")
async def health_check():
    """Health check per SLA monitoring"""
    return {
        "status": "ok",
        "message": "SLA Monitoring Service Active",
        "endpoints": [
            "GET /check-overdue - Controlla task scaduti",
            "GET /check-warnings - Controlla task in scadenza",
            "POST /run-escalation - Esegue check completo"
        ]
    }

@router.get("/check-overdue")
async def check_overdue_tasks(db: Session = Depends(get_db)):
    """Controlla task scaduti e invia escalation"""
    try:
        result = sla_escalation_service.check_overdue_tasks(db)
        logger.info(f"Overdue check completed: {result}")
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        logger.error(f"Error in overdue check: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

@router.get("/check-warnings")
async def check_warning_tasks(db: Session = Depends(get_db)):
    """Controlla task in scadenza e invia warning"""
    try:
        result = sla_escalation_service.check_warning_tasks(db)
        logger.info(f"Warning check completed: {result}")
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        logger.error(f"Error in warning check: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

@router.post("/run-escalation")
async def run_complete_escalation(db: Session = Depends(get_db)):
    """Esegue controllo completo: overdue + warning"""
    try:
        overdue_result = sla_escalation_service.check_overdue_tasks(db)
        warning_result = sla_escalation_service.check_warning_tasks(db)
        
        result = {
            "overdue": overdue_result,
            "warnings": warning_result,
            "total_escalations": overdue_result.get("escalations_sent", 0),
            "total_warnings": warning_result.get("warnings_sent", 0)
        }
        
        logger.info(f"Complete escalation run: {result}")
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        logger.error(f"Error in complete escalation: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
