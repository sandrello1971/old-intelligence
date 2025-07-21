from fastapi import APIRouter, Depends
from app.services.analytics_engine import analytics
from app.core.auth import get_current_user
import json

router = APIRouter()

@router.post("/chat_query_advanced")
async def advanced_chat_query(
    request: dict,
    current_user = Depends(get_current_user)
):
    """
    Endpoint avanzato per query NLM + Analytics
    """
    query = request.get("text", "")
    session_id = request.get("session_id", "")
    
    try:
        # Usa analytics engine invece di SQL diretto
        result = analytics.natural_language_to_sql(query)
        
        # Log per debugging
        print(f"🤖 Advanced Query: {query}")
        print(f"📊 Result Type: {result.get('type', 'unknown')}")
        
        return result
        
    except Exception as e:
        return {
            "type": "error",
            "summary": f"❌ Errore analytics: {str(e)}",
            "data": []
        }

@router.get("/kpi_dashboard")
async def get_kpi_dashboard(current_user = Depends(get_current_user)):
    """Endpoint dedicato per dashboard KPI"""
    try:
        return analytics._get_kpi_dashboard()
    except Exception as e:
        return {"error": str(e)}

@router.post("/generate_report")
async def generate_business_report(
    request: dict,
    current_user = Depends(get_current_user)
):
    """Genera report business automatico"""
    report_type = request.get("type", "monthly")
    
    # Implementa generazione report PDF/Excel
    return {"message": "Report generation not implemented yet"}
