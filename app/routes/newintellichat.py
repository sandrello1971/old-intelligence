from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from openai import OpenAI
import os
import json
from app.core.database import get_db
from matplotlib import pyplot as plt
import io
import base64
import pandas as pd
from uuid import UUID, uuid4
from typing import Union

router = APIRouter(tags=["intellichat"])

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo")

PRIORITY_MAP = {0: "bassa", 1: "media", 2: "alta"}
STATUS_MAP = {0: "aperto", 1: "sospeso", 2: "chiuso"}

# Memoria in RAM per persistenza temporanea
SESSION_CONTEXT = {}

class ChatText(BaseModel):
    session_id: Union[str, UUID]
    text: str

@router.get("/health")
def health_check():
    """Health check che verifica anche la connessione al database"""
    try:
        # Test connessione DB con database corretto
        db_session = next(get_db())
        result = db_session.execute(text("SELECT current_database(), COUNT(*) FROM tasks"))
        db_name, task_count = result.fetchone()
        db_session.close()
        
        return {
            "status": "online",
            "service": "IntelliChat BI",
            "database": db_name,
            "tasks_count": task_count,
            "openai_model": MODEL,
            "timestamp": pd.Timestamp.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "service": "IntelliChat BI", 
            "database": "disconnected",
            "error": str(e),
            "timestamp": pd.Timestamp.now().isoformat()
        }

@router.get("/kpi_dashboard")
def get_kpi_dashboard(db: Session = Depends(get_db)):
    """
    KPI Dashboard con dati reali dal database intelligence_db
    """
    try:
        print("🔍 Starting KPI dashboard calculation...")
        
        # Test database connection
        result = db.execute(text("SELECT current_database()"))
        current_db = result.fetchone()[0]
        print(f"✅ Connected to database: {current_db}")
        
        kpi_data = {}
        
        # Total tasks
        result = db.execute(text("SELECT COUNT(*) FROM tasks"))
        kpi_data["totalTasks"] = result.fetchone()[0]
        print(f"✅ Total tasks: {kpi_data['totalTasks']}")
        
        # Completed tasks (status = 'chiuso')
        result = db.execute(text("SELECT COUNT(*) FROM tasks WHERE status = 'chiuso'"))
        kpi_data["completedTasks"] = result.fetchone()[0]
        print(f"✅ Completed tasks: {kpi_data['completedTasks']}")
        
        # Open tasks (status = 'aperto')
        result = db.execute(text("SELECT COUNT(*) FROM tasks WHERE status = 'aperto'"))
        kpi_data["openTasks"] = result.fetchone()[0]
        print(f"✅ Open tasks: {kpi_data['openTasks']}")
        
        # Active users (distinct owners con tasks non chiusi)
        result = db.execute(text("SELECT COUNT(DISTINCT owner) FROM tasks WHERE status != 'chiuso'"))
        kpi_data["activeUsers"] = result.fetchone()[0]
        print(f"✅ Active users: {kpi_data['activeUsers']}")
        
        # Open tickets (status = 0)
        result = db.execute(text("SELECT COUNT(*) FROM tickets WHERE status = 0"))
        kpi_data["openTickets"] = result.fetchone()[0]
        print(f"✅ Open tickets: {kpi_data['openTickets']}")
        
        # Total tickets
        result = db.execute(text("SELECT COUNT(*) FROM tickets"))
        kpi_data["totalTickets"] = result.fetchone()[0]
        print(f"✅ Total tickets: {kpi_data['totalTickets']}")
        
        # Companies count
        result = db.execute(text("SELECT COUNT(*) FROM companies"))
        kpi_data["companiesCount"] = result.fetchone()[0]
        print(f"✅ Companies: {kpi_data['companiesCount']}")
        
        # Task status breakdown
        result = db.execute(text("SELECT status, COUNT(*) FROM tasks GROUP BY status"))
        task_status_breakdown = {row[0]: row[1] for row in result.fetchall()}
        print(f"✅ Task status breakdown: {task_status_breakdown}")
        
        # Completion rate
        total = kpi_data["totalTasks"]
        completed = kpi_data["completedTasks"]
        completion_rate = round((completed / total * 100), 1) if total > 0 else 0
        
        final_result = {
            "totalTasks": kpi_data["totalTasks"],
            "completedTasks": kpi_data["completedTasks"],
            "openTasks": kpi_data["openTasks"],
            "activeUsers": kpi_data["activeUsers"],
            "openTickets": kpi_data["openTickets"],
            "totalTickets": kpi_data["totalTickets"],
            "companiesCount": kpi_data["companiesCount"],
            "completionRate": completion_rate,
            "taskStatusBreakdown": task_status_breakdown,
            "databaseName": current_db,
            "lastUpdate": pd.Timestamp.now().isoformat()
        }
        
        print(f"🎯 Final KPI result: {final_result}")
        return final_result
        
    except Exception as e:
        print(f"🔥 KPI Dashboard Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Errore KPI dashboard: {str(e)}")

@router.post("/chat_query")
def chat_query(payload: ChatText, db: Session = Depends(get_db)):
    try:
        session = SESSION_CONTEXT.setdefault(str(payload.session_id), {"history": [], "last_df": None})

        full_prompt = """
Agisci come un analista dati esperto di CRM. Genera query SQL compatibili con PostgreSQL. Restituisci la risposta in JSON nel formato:
{
  "sql": "QUERY_SQL_HERE",
  "answer_mode": "discorsiva | tabellare | grafico | predittiva"
}

Usa answer_mode = "discorsiva" se la risposta è un singolo valore o una riga. answer_mode = "tabellare" se la risposta è tabellare. Usa "grafico" per distribuzioni, e "predittiva" per stime.

# SCHEMA DATABASE (intelligence_db)

## activities
- id, title, priority (text), description (text), status (text), company_id → companies.id
- owner_id, customer_name, milestone_id, sub_type_id → sub_types.id

## companies
- id, nome (nome azienda), partita_iva, address, sector

## tickets
- id, activity_id, company_id, milestone_id, owner_id → users.id
- status (int: 0=aperto, 1=sospeso, 2=chiuso), priority (int), detected_services (array), ticket_code
- Relazioni: company_id → companies.id

## tasks
- id, ticket_id → tickets.id
- status (text: 'aperto', 'chiuso'), priority, milestone_id → milestones.id
- owner → users.id

## users
- id, name, surname, email

## milestones
- id, name, project_type

## opportunities
- id, titolo, cliente, stato, categoria

## sub_types
- id, name, code

# NOTE IMPORTANTI:
- Usa `status = 0` solo per `tickets.status` (INT)
- Usa `status = 'aperto'` per `tasks.status` (TEXT)
- Per unire `tickets` e `companies`, usa: `tickets.company_id = companies.id`
- Per contare quanti task sono "aperti": `WHERE tasks.status = 'aperto'`
""".strip()

        if session["history"]:
            last = session["history"][-1]
            full_prompt += f"\nDomanda precedente: {last['question']}\nRisposta: {last['answer']}"

        full_prompt += f"\nDomanda: {payload.text}"

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "Sei un assistente SQL esperto per CRM. Fai attenzione al tipo dei campi."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.2
        )

        reply = response.choices[0].message.content.strip()

        if reply.startswith("```json"):
            reply = reply.strip("`").strip("json").strip()

        try:
            parsed = json.loads(reply)
        except json.JSONDecodeError:
            import ast
            parsed = ast.literal_eval(reply)
            if isinstance(parsed, str):
                parsed = json.loads(parsed)

        sql = parsed.get("sql")
        mode = parsed.get("answer_mode")

        if not sql or not mode:
            raise HTTPException(status_code=422, detail="Risposta GPT incompleta o malformata")

        print(f"[SQL] {sql}")  # debug log

        result = db.execute(text(sql))
        rows = result.fetchall()
        columns = result.keys()
        df = pd.DataFrame(rows, columns=columns)

        for col in df.columns:
            if "priority" in col:
                df[col] = df[col].map(PRIORITY_MAP).fillna(df[col])
            if "status" in col and df[col].dtype in [int, float]:
                df[col] = df[col].map(STATUS_MAP).fillna(df[col])

        session["history"].append({"question": payload.text, "answer": reply})
        session["last_df"] = df

        if mode == "tabellare":
            if df.shape == (1, 1):
                mode = "discorsiva"
            else:
                return df.to_dict(orient="records")

        if mode == "grafico":
            img = io.BytesIO()
            df.select_dtypes(include=['object', 'category']).apply(lambda x: x.value_counts()).T.plot(kind='bar')
            plt.tight_layout()
            plt.savefig(img, format='png')
            plt.close()
            img.seek(0)
            b64 = base64.b64encode(img.read()).decode("utf-8")
            return {"image_base64": b64}

        if mode == "discorsiva":
            if df.shape == (1, 1):
                col = df.columns[0]
                val = df.iat[0, 0]
                desc_prompt = (
                    f"L'utente ha chiesto: \"{payload.text}\"\n"
                    f"Il valore di risposta è: {col} = {val}\n"
                    f"Restituisci una risposta breve in italiano, naturale, discorsiva, senza codice né spiegazioni tecniche."
                )
                follow_up = client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "user", "content": desc_prompt}]
                )
                return {"summary": follow_up.choices[0].message.content.strip()}

            desc_prompt = f"Descrivi in italiano il significato della seguente tabella:\n{df.to_string()}"
            follow_up = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": desc_prompt}]
            )
            return {"summary": follow_up.choices[0].message.content.strip()}

        if mode == "predittiva":
            return {"warning": "Predizione non ancora implementata"}

        return {"summary": "Nessun dato utile trovato."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat_query_advanced")
def chat_query_advanced(payload: ChatText, db: Session = Depends(get_db)):
    """
    Endpoint avanzato che wrappa il chat_query esistente per supportare diversi tipi di output
    """
    try:
        query_lower = payload.text.lower()
        
        if any(keyword in query_lower for keyword in ['dashboard', 'kpi']):
            dashboard_data = get_kpi_dashboard(db)
            return {
                "type": "dashboard",
                "data": dashboard_data,
                "summary": f"Dashboard KPI dal database {dashboard_data.get('databaseName', 'intelligence_db')}: {dashboard_data['totalTasks']} task totali, {dashboard_data['completedTasks']} completati."
            }
        
        # Usa il tuo sistema esistente per tutto il resto
        standard_response = chat_query(payload, db)
        
        if isinstance(standard_response, list):
            return {"type": "table", "data": standard_response}
        elif isinstance(standard_response, dict):
            if "image_base64" in standard_response:
                return {"type": "chart", "chart": standard_response}
            else:
                return standard_response
        else:
            return {"type": "text", "summary": str(standard_response)}
                
    except Exception as e:
        print(f"Errore chat_query_advanced: {e}")
        raise HTTPException(status_code=500, detail=str(e))
