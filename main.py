# 📉 Nuovo main.py corretto

from app.routes import dashboard
from fastapi import FastAPI
from app.core.database import Base, engine
from app.routes import tickets
from app.routes.tasks import router as tasks_router
from app.routes.owners import router as owners_router
from app.routes.phase_templates import router as phase_template_router
from app.routes import milestones as milestone_router
from app.routes.treeview_M24 import router as treeview_m24_router
from app.routes import crm_opportunity
from app.routes import crm_links
from app.routes import owners
from app.routes.tree import router as company_tree_router
from app.services.services import router as services_router
from app.routes import crm_generate
from app.routes import opportunities
from app.routes import sync
from app.routes import hashtags
from app.routes import dashboard_api
from app.routes import statistics
from dotenv import load_dotenv
from app.routes import sync
from fastapi.routing import APIRoute
from app.routes.newintellivoice import router as ulisse_voice_router
from app.routes.activities import router as activities_router
from app.routes.export import router as export_router
from app.routes import statistics_global
from starlette.middleware.sessions import SessionMiddleware
from app.routes.tickets import router as ticket_router
from app.routes.intellichat import router as intellichat_router
from app.auth.google import router as google_auth_router
from app.routes import local_auth
from app.routes.sla_monitoring import router as sla_monitoring_router

import app.models  # ⬅️ Devi aggiungere questo!

import logging
from app.logging_config import setup_logging
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

load_dotenv()

setup_logging()
logging.basicConfig(level=logging.DEBUG)

app = FastAPI()

@app.get("/api/auth/logi")
def fake_login(next: str = "/dashboard"):
    return {"status": "🔓 fake login disabilitato", "next": next}

# Crea le tabelle se non esistono
# Base.metadata.create_all(bind=engine)

# ✅ Include correttamente tutte le routes
app.include_router(dashboard.router)
app.include_router(tickets.router, prefix="/api")
app.include_router(tasks_router, prefix="/api")
app.include_router(owners_router, prefix="/api")
app.include_router(phase_template_router, prefix="/api/phase-templates")
app.include_router(milestone_router.router, prefix="/api")
app.include_router(crm_opportunity.router, prefix="/api")
app.include_router(crm_links.router, prefix="/api")
app.include_router(owners.router)
app.include_router(treeview_m24_router)
app.include_router(company_tree_router, prefix="/api")  # 🔄 corretto router tree
app.include_router(services_router, prefix="/api")
app.include_router(crm_generate.router)
app.include_router(opportunities.router, prefix="/api")
app.include_router(sync.router, prefix="/api")
app.include_router(hashtags.router)
app.include_router(statistics.router)
app.include_router(sync.router)
app.include_router(ulisse_voice_router, prefix="/api")
app.include_router(activities_router, prefix="/api")
app.include_router(export_router, prefix="/api")  # 👈 Registra il router
app.include_router(statistics_global.router, prefix="/api")
app.include_router(google_auth_router)
app.include_router(ticket_router)
app.include_router(intellichat_router, prefix="/api/intellichat")
app.include_router(local_auth.router, prefix="/api")
app.include_router(local_auth.router, prefix="/api")
app.include_router(sla_monitoring_router, tags=["SLA Monitoring"])  # ← AGGIUNGI QUESTA

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY", "B4b4in4_07"),
    same_site="lax",     # ⛔ meno sicuro, solo per debug
    https_only=False     # ⛔ solo se non sei su HTTPS locale
)



# ✅ Serve i file statici di React
app.mount("/dashboard", StaticFiles(directory="app/static", html=True), name="dashboard")
app.mount("/dashboard/static", StaticFiles(directory="app/static/static"), name="static")

for route in app.routes:
    if isinstance(route, APIRoute):
        print(f"{route.path} [{route.methods}]")

@app.get("/")
def read_root():
    return {"message": "Intelligence AI is running."}

@app.get("/dashboard/{path_name:path}")
def serve_react_app(path_name: str):
    index_path = os.path.join("app", "static", "index.html")
    return FileResponse(index_path)

# ===== BUSINESS CARDS ROUTES DIRETTE =====
from fastapi import UploadFile, File, Form, HTTPException
from typing import Optional, List
import json, uuid, base64, io
from datetime import datetime
from pydantic import BaseModel
from PIL import Image



# ===== BUSINESS CARDS API =====
@app.get("/api/business_cards/test")
def business_cards_test():
    print("🔍 BUSINESS CARDS TEST FUNCTION DEFINITA")
    return {"message": "Business cards API OK", "status": "working"}

@app.get("/api/business_cards/stats") 
def business_cards_stats():
    return {
        "business_cards": {"total": 0, "successful": 0, "avg_confidence": 0, "avg_processing_time": 0},
        "contacts": {"total": 0, "unique_companies": 0, "with_email": 0, "with_phone": 0}
    }

@app.get("/api/business_cards/contacts")
def business_cards_contacts():
    return []

# ===== ROUTES SERVIZI (CORRETTE - NO DOPPIO PREFIX) =====
try:
    # Import con percorsi specifici per evitare conflitti
    from app.routes.sub_types import router as sub_types_router
    from app.routes.service_users import router as service_users_router
    from app.routes.services_tree import router as services_tree_router
    
    # ✅ CORREZIONE: No prefix per services_tree_router perché ce l'ha già
    app.include_router(sub_types_router, prefix="/api", tags=["Services Management"])
    app.include_router(service_users_router, prefix="/api", tags=["Service Users"])
    app.include_router(services_tree_router, tags=["Services Tree"])  # ⬅️ NESSUN PREFIX!
    
    print("✅ Routes servizi caricate con successo - PREFIX CORRETTI")
except ImportError as e:
    print(f"⚠️ Routes servizi non disponibili: {e}")
except Exception as e:
    print(f"⚠️ Errore caricamento routes servizi: {e}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check per monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": {
            "database": "ok",
            "api": "ok", 
            "services_management": "ok"
        }
    }

@app.get("/api/health")
async def api_health_check():
    """Health check API specifico"""
    return {"status": "ok", "api_version": "1.0"}

# ✅ INCLUDE FORZATO SERVICES TREE - FINALE
print("🔧 Caricamento router services_tree...")
try:
    from app.routes.services_tree import router as final_services_tree_router
    app.include_router(final_services_tree_router, tags=["Final Services Tree"])
    print("✅ SERVICES TREE ROUTER INCLUSO CON SUCCESSO!")
    print(f"🎯 Routes aggiunte: {len(final_services_tree_router.routes)}")
except Exception as e:
    print(f"❌ Errore include services_tree: {e}")
    import traceback
    traceback.print_exc()

# ✅ INCLUDE SERVICES TREE ROUTER (VERSIONE FUNZIONANTE)
print("🔧 Caricamento router services_tree...")
try:
    from app.routes.services_tree import router as final_services_tree_router
    app.include_router(final_services_tree_router, tags=["Final Services Tree"])
    print("✅ SERVICES TREE ROUTER INCLUSO CON SUCCESSO!")
except Exception as e:
    print(f"❌ Errore include services_tree: {e}")
