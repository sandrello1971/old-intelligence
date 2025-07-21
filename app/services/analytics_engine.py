import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
import json
import plotly.graph_objects as go
import plotly.express as px
from sqlalchemy.orm import Session
from app.core.database import SessionLocal

class AnalyticsEngine:
    def __init__(self):
        self.session = SessionLocal()
    
    def natural_language_to_sql(self, query: str) -> dict:
        """
        Converte linguaggio naturale in SQL con context awareness
        """
        # Mapping intelligente per business queries
        query_lower = query.lower()
        
        # Analisi trend temporali
        if any(word in query_lower for word in ["trend", "crescita", "andamento", "negli ultimi"]):
            if "mesi" in query_lower:
                return self._get_monthly_trends()
            elif "settimane" in query_lower:
                return self._get_weekly_trends()
        
        # Top performers
        elif any(word in query_lower for word in ["top", "migliori", "peggiori"]):
            if "aziend" in query_lower:
                return self._get_top_companies()
            elif "utent" in query_lower or "owner" in query_lower:
                return self._get_top_users()
        
        # Predictions
        elif any(word in query_lower for word in ["previsioni", "forecast", "predici"]):
            return self._generate_forecasts()
        
        # KPI Dashboard
        elif any(word in query_lower for word in ["dashboard", "kpi", "metriche"]):
            return self._get_kpi_dashboard()
        
        # Fallback to basic SQL
        else:
            return self._basic_sql_query(query)
    
    def _get_monthly_trends(self):
        sql = """
        SELECT 
            DATE_TRUNC('month', creation_date::timestamp) as mese,
            COUNT(*) as attivita_create,
            COUNT(DISTINCT customer_id) as aziende_coinvolte,
            AVG(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) * 100 as completion_rate
        FROM activities 
        WHERE creation_date >= NOW() - INTERVAL '12 months'
        GROUP BY DATE_TRUNC('month', creation_date::timestamp)
        ORDER BY mese
        """
        
        result = self.session.execute(sql).fetchall()
        
        # Genera grafico con Plotly
        df = pd.DataFrame(result, columns=['mese', 'attivita_create', 'aziende_coinvolte', 'completion_rate'])
        
        fig = px.line(df, x='mese', y=['attivita_create', 'aziende_coinvolte'], 
                     title="📈 Trend Attività Mensili")
        
        return {
            "type": "chart",
            "data": df.to_dict('records'),
            "chart": fig.to_json(),
            "summary": f"Analisi di {len(df)} mesi con media {df['attivita_create'].mean():.1f} attività/mese"
        }
    
    def _get_top_companies(self):
        sql = """
        SELECT 
            c.nome as azienda,
            COUNT(a.id) as totale_attivita,
            COUNT(CASE WHEN a.status = 'completed' THEN 1 END) as completate,
            COUNT(CASE WHEN a.status = 'open' THEN 1 END) as aperte,
            ROUND(AVG(CASE WHEN a.status = 'completed' THEN 1 ELSE 0 END) * 100, 2) as success_rate
        FROM companies c
        LEFT JOIN activities a ON c.id = a.company_id
        GROUP BY c.id, c.nome
        HAVING COUNT(a.id) > 0
        ORDER BY totale_attivita DESC
        LIMIT 10
        """
        
        result = self.session.execute(sql).fetchall()
        df = pd.DataFrame(result, columns=['azienda', 'totale_attivita', 'completate', 'aperte', 'success_rate'])
        
        # Grafico a barre
        fig = px.bar(df, x='azienda', y='totale_attivita', 
                    title="🏆 Top 10 Aziende per Attività")
        
        return {
            "type": "chart",
            "data": df.to_dict('records'),
            "chart": fig.to_json(),
            "summary": f"Top azienda: {df.iloc[0]['azienda']} con {df.iloc[0]['totale_attivita']} attività"
        }
    
    def _generate_forecasts(self):
        """
        Genera previsioni usando ML
        """
        # Dati storici attività per mese
        sql = """
        SELECT 
            EXTRACT(EPOCH FROM DATE_TRUNC('month', creation_date::timestamp)) as timestamp,
            COUNT(*) as attivita_count
        FROM activities 
        WHERE creation_date >= NOW() - INTERVAL '24 months'
        GROUP BY DATE_TRUNC('month', creation_date::timestamp)
        ORDER BY timestamp
        """
        
        result = self.session.execute(sql).fetchall()
        df = pd.DataFrame(result, columns=['timestamp', 'attivita_count'])
        
        if len(df) < 3:
            return {"error": "Dati insufficienti per previsioni"}
        
        # Preparazione dati per ML
        X = df['timestamp'].values.reshape(-1, 1)
        y = df['attivita_count'].values
        
        # Scaler per normalizzazione
        scaler_X = StandardScaler()
        X_scaled = scaler_X.fit_transform(X)
        
        # Modello di regressione lineare
        model = LinearRegression()
        model.fit(X_scaled, y)
        
        # Previsioni prossimi 6 mesi
        future_timestamps = []
        last_timestamp = df['timestamp'].max()
        for i in range(1, 7):
            future_timestamps.append(last_timestamp + (i * 30 * 24 * 3600))  # +30 giorni
        
        future_X = np.array(future_timestamps).reshape(-1, 1)
        future_X_scaled = scaler_X.transform(future_X)
        predictions = model.predict(future_X_scaled)
        
        # Combina dati storici + previsioni
        forecast_df = pd.DataFrame({
            'periodo': [datetime.fromtimestamp(ts).strftime('%Y-%m') for ts in future_timestamps],
            'previsione_attivita': predictions.astype(int),
            'tipo': ['forecast'] * len(predictions)
        })
        
        # Grafico combinato
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[datetime.fromtimestamp(ts).strftime('%Y-%m') for ts in df['timestamp']], 
            y=df['attivita_count'],
            mode='lines+markers',
            name='Storico',
            line=dict(color='blue')
        ))
        fig.add_trace(go.Scatter(
            x=forecast_df['periodo'], 
            y=forecast_df['previsione_attivita'],
            mode='lines+markers',
            name='Previsione',
            line=dict(color='red', dash='dash')
        ))
        fig.update_layout(title="🔮 Forecast Attività Prossimi 6 Mesi")
        
        return {
            "type": "forecast",
            "data": forecast_df.to_dict('records'),
            "chart": fig.to_json(),
            "summary": f"Previsione media: {predictions.mean():.1f} attività/mese (R²: {model.score(X_scaled, y):.3f})"
        }
    
    def _get_kpi_dashboard(self):
        """
        Dashboard KPI business critical
        """
        kpis = {}
        
        # KPI 1: Attività questo mese vs mese scorso
        sql_current = "SELECT COUNT(*) FROM activities WHERE creation_date >= DATE_TRUNC('month', NOW())"
        sql_previous = """SELECT COUNT(*) FROM activities 
                         WHERE creation_date >= DATE_TRUNC('month', NOW() - INTERVAL '1 month')
                         AND creation_date < DATE_TRUNC('month', NOW())"""
        
        current_month = self.session.execute(sql_current).scalar()
        previous_month = self.session.execute(sql_previous).scalar()
        growth_rate = ((current_month - previous_month) / previous_month * 100) if previous_month > 0 else 0
        
        kpis['attivita_mensili'] = {
            'valore': current_month,
            'precedente': previous_month,
            'crescita_pct': round(growth_rate, 1),
            'trend': '📈' if growth_rate > 0 else '📉'
        }
        
        # KPI 2: Tasso completamento
        sql_completion = """
        SELECT 
            COUNT(CASE WHEN status = 'completed' THEN 1 END) * 100.0 / COUNT(*) as completion_rate
        FROM activities 
        WHERE creation_date >= NOW() - INTERVAL '30 days'
        """
        completion_rate = self.session.execute(sql_completion).scalar() or 0
        
        kpis['completion_rate'] = {
            'valore': round(completion_rate, 1),
            'target': 85.0,
            'status': '✅' if completion_rate >= 85 else '⚠️'
        }
        
        # KPI 3: Distribuzione servizi
        sql_services = """
        SELECT 
            jsonb_array_elements_text(detected_services) as servizio,
            COUNT(*) as count
        FROM activities 
        WHERE detected_services IS NOT NULL 
        AND creation_date >= NOW() - INTERVAL '30 days'
        GROUP BY servizio
        ORDER BY count DESC
        LIMIT 5
        """
        services_result = self.session.execute(sql_services).fetchall()
        services_df = pd.DataFrame(services_result, columns=['servizio', 'count'])
        
        # Grafico a torta servizi
        fig_pie = px.pie(services_df, values='count', names='servizio', 
                        title="🥧 Distribuzione Servizi (30gg)")
        
        return {
            "type": "dashboard",
            "kpis": kpis,
            "services_chart": fig_pie.to_json(),
            "services_data": services_df.to_dict('records'),
            "summary": f"Dashboard aggiornato: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        }
    
    def _basic_sql_query(self, query: str):
        """Fallback per query SQL standard"""
        # Qui implementeresti la logica SQL esistente
        return {"type": "table", "data": [], "summary": "Query SQL standard"}

# Istanza globale
analytics = AnalyticsEngine()
