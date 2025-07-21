"""
Assessment Service - Business Logic Layer
Data: 2025-06-16
Versione: 1.0
"""

from typing import Dict, List, Optional, Any
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.assessment.models.assessment import (
    AssessmentSession, AssessmentResult, AssessmentResponse, AssessmentBenchmarkData
)
from app.models import Company, User  # Solo lettura dal core

class AssessmentService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_session(self, company_id: int, user_id: Optional[str] = None) -> AssessmentSession:
        """Crea nuova sessione assessment"""
        # Ottieni nome company (solo lettura)
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise ValueError(f"Company {company_id} not found")
        
        session = AssessmentSession(
            company_id=company_id,
            user_id=user_id,
            session_code=f"ASMT_{company_id}_{int(datetime.now().timestamp())}",
            company_name=company.nome,
            status="draft"
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def get_companies_list(self) -> List[Dict]:
        """Ottieni lista aziende per assessment (solo lettura)"""
        companies = self.db.query(Company).all()
        return [{"id": c.id, "name": c.nome, "sector": c.sector} for c in companies]
    
    def get_assessment_structure(self) -> Dict:
        """Restituisce struttura completa assessment basata su Excel"""
        return {
            "title": "Digital Maturity Assessment",
            "description": "Valutazione della maturità digitale basata su standard europei",
            "sections": [
                {
                    "code": "M2.1",
                    "title": "Strategia Imprenditoriale Digitale",
                    "description": "Valutazione investimenti digitalizzazione per area business",
                    "type": "investment_strategy",
                    "questions": self._get_m21_questions()
                },
                {
                    "code": "M2.2", 
                    "title": "Preparazione Digitale",
                    "description": "Tecnologie e soluzioni digitali in uso",
                    "type": "technology_readiness",
                    "questions": self._get_m22_questions()
                },
                {
                    "code": "M2.3",
                    "title": "Digitalizzazione Antropocentrica", 
                    "description": "Competenze e formazione del personale",
                    "type": "human_capabilities",
                    "questions": self._get_m23_questions()
                },
                {
                    "code": "M2.4",
                    "title": "Gestione Dati e Connessione",
                    "description": "Politiche e gestione dei dati aziendali", 
                    "type": "data_management",
                    "questions": self._get_m24_questions()
                },
                {
                    "code": "M2.5",
                    "title": "Automazione e Intelligenza Artificiale",
                    "description": "Tecnologie AI e automazione in uso",
                    "type": "ai_automation", 
                    "questions": self._get_m25_questions()
                },
                {
                    "code": "M2.6",
                    "title": "Digitalizzazione Verde",
                    "description": "Sostenibilità ambientale tramite digitale",
                    "type": "green_digitalization",
                    "questions": self._get_m26_questions()
                }
            ]
        }
    
    def _get_m21_questions(self) -> List[Dict]:
        """M2.1 - Strategia Imprenditoriale Digitale"""
        areas = [
            "progettazione di prodotti/servizi (tra cui ricerca, sviluppo e innovazione)",
            "pianificazione e gestione di progetti", 
            "operazioni (produzione di beni fisici/fabbricazione, imballaggio, manutenzione, servizi ecc.)",
            "collaborazione con altre sedi interne o altre imprese nella catena del valore",
            "logistica in entrata e deposito",
            "marketing, servizi di vendita e servizi ai clienti (gestione dei clienti, elaborazione degli ordini, helpdesk ecc.)",
            "consegna (logistica in uscita, fatture elettroniche ecc.)",
            "amministrazione e risorse umane",
            "acquisti e appalti"
        ]
        
        return [
            {
                "id": f"m21_{i+1}",
                "text": area,
                "type": "checkbox",
                "required": False,
                "options": [
                    {"value": "invested", "label": "Già Investito", "score": 10},
                    {"value": "planned", "label": "Prevede di Investire", "score": 5}
                ]
            }
            for i, area in enumerate(areas)
        ]
    
    def _get_m22_questions(self) -> List[Dict]:
        """M2.2 - Preparazione Digitale"""
        technologies = [
            "infrastrutture di connettività (internet ad alta velocità (fibra), servizi di cloud computing, accesso remoto ai sistemi d'ufficio)",
            "sito web dell'impresa",
            "moduli e blog/forum basati sul web per comunicare con i clienti", 
            "chat dal vivo, social network e chatbot per comunicare con i clienti",
            "vendite tramite il commercio elettronico (da impresa a consumatore, da impresa a impresa)",
            "promozione mediante marketing elettronico (annunci online, social media per le imprese ecc.)",
            "e-government (interazione online con le autorità pubbliche, anche per gli appalti pubblici)",
            "strumenti di collaborazione tra imprese a distanza (ad esempio piattaforma di telelavoro, videoconferenza, apprendimento virtuale, strumenti specifici dell'impresa)",
            "portale web interno (Intranet)",
            "gestione delle relazioni con i clienti (CRM)",
            "gestione della catena di fornitura (SCM)",
            "pianificazione delle risorse aziendali (ERP)",
            "condivisione di informazioni sui prodotti in formato elettronico",
            "integrazione di sistemi interni di gestione delle informazioni aziendali",
            "condivisione elettronica di informazioni con fornitori e clienti (estrazione automatica di dati)",
            "software di gestione del magazzino (WMS)",
            "monitoraggio della sicurezza informatica",
            "analisi dei big data",
            "tecnologie emergenti (IoT, blockchain, realtà aumentata/virtuale)"
        ]
        
        return [
            {
                "id": f"m22_{i+1}",
                "text": tech,
                "type": "checkbox",
                "required": False,
                "options": [
                    {"value": "implemented", "label": "Implementato", "score": 10}
                ]
            }
            for i, tech in enumerate(technologies)
        ]
    
    def _get_m23_questions(self) -> List[Dict]:
        """M2.3 - Digitalizzazione Antropocentrica"""
        capabilities = [
            "effettua una valutazione delle competenze del personale per individuarne le carenze",
            "elabora un piano di formazione per formare e migliorare le competenze del personale",
            "organizza brevi corsi di formazione, fornisce tutorial/orientamenti e altre risorse di e-learning",
            "favorisce le opportunità di apprendimento attraverso la pratica/l'apprendimento tra pari/la sperimentazione",
            "offre tirocini e inserimenti professionali in settori concernenti capacità chiave",
            "promuove la partecipazione del personale a corsi di formazioni organizzati da enti esterni",
            "si avvale di programmi sovvenzionati di formazione e miglioramento delle competenze"
        ]
        
        return [
            {
                "id": f"m23_{i+1}",
                "text": cap,
                "type": "checkbox", 
                "required": False,
                "options": [
                    {"value": "implemented", "label": "Implementato", "score": 10}
                ]
            }
            for i, cap in enumerate(capabilities)
        ]
    
    def _get_m24_questions(self) -> List[Dict]:
        """M2.4 - Gestione Dati e Connessione"""
        data_management = [
            "L'organizzazione ha messo in atto una politica/un piano/una serie di misure per la gestione dei dati",
            "i dati pertinenti sono archiviati in formato digitale",
            "i dati sono adeguatamente integrati anche quando sono distribuiti tra diversi sistemi",
            "i dati sono accessibili in tempo reale da dispositivi e luoghi diversi",
            "i dati raccolti sono sistematicamente analizzati e comunicati ai fini del processo decisionale",
            "l'analisi dei dati è arricchita combinando fonti esterne con dati propri",
            "l'analisi dei dati è accessibile senza bisogno di assistenza specialistica"
        ]
        
        return [
            {
                "id": f"m24_{i+1}",
                "text": dm,
                "type": "checkbox",
                "required": False,
                "options": [
                    {"value": "implemented", "label": "Implementato", "score": 10}
                ]
            }
            for i, dm in enumerate(data_management)
        ]
    
    def _get_m25_questions(self) -> List[Dict]:
        """M2.5 - Automazione e Intelligenza Artificiale"""
        ai_technologies = [
            "elaborazione del linguaggio naturale, compresi chatbot, text mining, traduzione automatica, analisi del sentiment",
            "visione computerizzata/riconoscimento dell'immagine", 
            "elaborazione audio/riconoscimento, elaborazione e sintesi vocali",
            "robotica e dispositivi autonomi",
            "business intelligence, analisi dei dati, sistemi di supporto alle decisioni, sistemi di raccomandazione, sistemi di controllo intelligenti"
        ]
        
        return [
            {
                "id": f"m25_{i+1}",
                "text": ai_tech,
                "type": "scale",
                "required": False,
                "scale_min": 0,
                "scale_max": 5,
                "scale_labels": {
                    "0": "Non utilizzate",
                    "1": "Utilizzo in fase di valutazione",
                    "2": "In fase di prototipazione", 
                    "3": "In fase di collaudo",
                    "4": "In fase di attuazione",
                    "5": "Operative"
                }
            }
            for i, ai_tech in enumerate(ai_technologies)
        ]
    
    def _get_m26_questions(self) -> List[Dict]:
        """M2.6 - Digitalizzazione Verde"""
        green_initiatives = [
            "modello aziendale sostenibile (ad esempio modello di economia circolare, prodotto come servizio)",
            "fornitura di servizi sostenibili (ad esempio tracciamento dell'utilizzo per un ulteriore riutilizzo da parte di altri utenti)",
            "prodotti sostenibili (ad esempio progettazione ecocompatibile, pianificazione del ciclo di vita dei prodotti end-to-end)",
            "metodi, materiali e componenti di produzione e fabbricazione sostenibili",
            "emissioni, inquinamento e/o gestione dei rifiuti",
            "produzione di energia sostenibile nel proprio impianto",
            "ottimizzazione del consumo/costo delle materie prime",
            "riduzione dei costi di trasporto e imballaggio",
            "applicazioni digitali per incoraggiare un comportamento responsabile dei consumatori"
        ]
        
        return [
            {
                "id": f"m26_{i+1}",
                "text": green,
                "type": "checkbox",
                "required": False,
                "options": [
                    {"value": "implemented", "label": "Implementato", "score": 10}
                ]
            }
            for i, green in enumerate(green_initiatives)
        ]
    
    def submit_assessment(self, session_id: int, responses: Dict) -> Dict:
        """Elabora e salva risultati assessment"""
        session = self.db.query(AssessmentSession).filter_by(id=session_id).first()
        if not session:
            raise ValueError("Session not found")
        
        # Calcola punteggi per ogni area
        results = {}
        
        # Raggruppa risposte per area
        responses_by_area = {}
        for question_id, response_data in responses.items():
            area_code = question_id.split('_')[0].upper()  # m21 -> M2.1
            if area_code.startswith('M2'):
                area_code = area_code[:2] + '.' + area_code[2:]  # M21 -> M2.1
            
            if area_code not in responses_by_area:
                responses_by_area[area_code] = []
            responses_by_area[area_code].append({
                'question_id': question_id,
                'data': response_data
            })
        
        for area_code, area_responses in responses_by_area.items():
            score = self._calculate_area_score(area_code, area_responses)
            results[area_code] = score
            
            # Salva risultato
            result = AssessmentResult(
                session_id=session_id,
                area_code=area_code,
                area_name=self._get_area_name(area_code),
                score=score['score'],
                max_score=score['max_score'],
                percentage=score['percentage'],
                maturity_level=score['maturity_level'],
                benchmark_score=score.get('benchmark_score'),
                gap_analysis=score.get('gap_analysis')
            )
            self.db.add(result)
        
        # Salva risposte dettagliate
        for question_id, response_data in responses.items():
            area_code = question_id.split('_')[0].upper()
            if area_code.startswith('M2'):
                area_code = area_code[:2] + '.' + area_code[2:]
            
            response = AssessmentResponse(
                session_id=session_id,
                question_id=question_id,
                question_text=self._get_question_text(question_id),
                area_code=area_code,
                answer_type=response_data.get('type', 'unknown'),
                selected_values=response_data.get('selected', []),
                score=self._calculate_question_score(question_id, response_data)
            )
            self.db.add(response)
        
        # Aggiorna sessione
        session.status = "completed"
        session.completed_at = datetime.now()
        
        self.db.commit()
        
        # Genera raccomandazioni AI
        recommendations = self._generate_ai_recommendations(results)
        benchmark_comparison = self._get_benchmark_comparison(results)
        
        return {
            "session_id": session_id,
            "company_name": session.company_name,
            "results": results,
            "overall_score": self._calculate_overall_score(results),
            "recommendations": recommendations,
            "benchmark_comparison": benchmark_comparison,
            "next_steps": self._generate_next_steps(results),
            "radar_data": self._generate_radar_data(results, benchmark_comparison)
        }
    
    def _calculate_area_score(self, area_code: str, responses: List[Dict]) -> Dict:
        """Calcola punteggio per area specifica"""
        total_score = 0
        max_possible = 0
        
        for response in responses:
            response_data = response['data']
            
            if area_code in ["M2.1", "M2.2", "M2.3", "M2.4", "M2.6"]:
                # Checkbox scoring
                selected = response_data.get("selected", [])
                if "invested" in selected:
                    total_score += 10
                elif "planned" in selected:
                    total_score += 5
                elif "implemented" in selected:
                    total_score += 10
                max_possible += 10
                
            elif area_code == "M2.5":
                # Scale scoring (0-5)
                scale_value = response_data.get("scale_value", 0)
                total_score += scale_value * 2  # Normalizza a 10
                max_possible += 10
        
        percentage = (total_score / max_possible * 100) if max_possible > 0 else 0
        maturity_level = self._determine_maturity_level(percentage)
        
        # Ottieni benchmark per confronto
        benchmark_score = self._get_area_benchmark(area_code)
        gap_analysis = percentage - benchmark_score if benchmark_score else None
        
        return {
            "score": total_score,
            "max_score": max_possible,
            "percentage": round(percentage, 2),
            "maturity_level": maturity_level,
            "benchmark_score": benchmark_score,
            "gap_analysis": round(gap_analysis, 2) if gap_analysis else None
        }
    
    def _determine_maturity_level(self, percentage: float) -> str:
        """Determina livello maturità da percentuale"""
        if percentage >= 80:
            return "expert"
        elif percentage >= 60:
            return "advanced" 
        elif percentage >= 40:
            return "intermediate"
        else:
            return "beginner"
    
    def _get_area_name(self, area_code: str) -> str:
        """Ottieni nome area da codice"""
        area_names = {
            "M2.1": "Strategia Imprenditoriale Digitale",
            "M2.2": "Preparazione Digitale",
            "M2.3": "Digitalizzazione Antropocentrica",
            "M2.4": "Gestione Dati e Connessione",
            "M2.5": "Automazione e Intelligenza Artificiale",
            "M2.6": "Digitalizzazione Verde"
        }
        return area_names.get(area_code, area_code)
    
    def _get_area_benchmark(self, area_code: str) -> Optional[float]:
        """Ottieni benchmark per area (media Italia)"""
        benchmark = self.db.query(AssessmentBenchmarkData).filter_by(
            industry="Italia",
            area_code=area_code
        ).first()
        return float(benchmark.average_score) if benchmark else None
    
    def _get_benchmark_comparison(self, results: Dict) -> Dict:
        """Confronta risultati con benchmark industria"""
        comparison = {}
        
        for area_code, score_data in results.items():
            # Ottieni tutti i benchmark per quest'area
            benchmarks = self.db.query(AssessmentBenchmarkData).filter_by(
                area_code=area_code
            ).all()
            
            comparison[area_code] = {
                "your_score": score_data['percentage'],
                "benchmarks": {}
            }
            
            for benchmark in benchmarks:
                comparison[area_code]["benchmarks"][benchmark.industry] = {
                    "average_score": float(benchmark.average_score),
                    "gap": score_data['percentage'] - float(benchmark.average_score),
                    "position": "above_average" if score_data['percentage'] > float(benchmark.average_score) else "below_average"
                }
        
        return comparison
    
    def _generate_ai_recommendations(self, results: Dict) -> List[str]:
        """Genera raccomandazioni AI personalizzate"""
        recommendations = []
        
        # Analizza punti deboli
        weak_areas = [area for area, score in results.items() if score['percentage'] < 50]
        strong_areas = [area for area, score in results.items() if score['percentage'] >= 70]
        
        # Raccomandazioni specifiche per area
        if "M2.1" in weak_areas:
            recommendations.append("Sviluppare una strategia digitale più strutturata con investimenti mirati in aree chiave come R&D e customer service.")
        
        if "M2.2" in weak_areas:
            recommendations.append("Implementare tecnologie digitali base come CRM, ERP e soluzioni cloud per migliorare l'efficienza operativa.")
        
        if "M2.3" in weak_areas:
            recommendations.append("Investire nella formazione digitale del personale con programmi strutturati di upskilling e reskilling.")
        
        if "M2.4" in weak_areas:
            recommendations.append("Implementare politiche di gestione dati e sistemi di business intelligence per decisioni data-driven.")
        
        if "M2.5" in weak_areas:
            recommendations.append("Esplorare tecnologie AI e automazione per ottimizzare processi e migliorare l'efficienza.")
        
        if "M2.6" in weak_areas:
            recommendations.append("Integrare sostenibilità e digitale per creare valore condiviso e rispondere alle esigenze ESG.")
        
        # Raccomandazioni per aree forti
        if strong_areas:
            recommendations.append(f"Continuare a investire nelle aree di forza: {', '.join([self._get_area_name(area) for area in strong_areas[:2]])}.")
        
        # Raccomandazione finale sempre presente
        recommendations.append("Consigliamo vivamente un assessment approfondito con EndUser Digital per sviluppare una roadmap personalizzata di trasformazione digitale.")
        
        return recommendations
    
    def _generate_next_steps(self, results: Dict) -> List[Dict]:
        """Genera next steps specifici"""
        next_steps = [
            {
                "priority": "high",
                "action": "Contatta EndUser Digital per assessment approfondito",
                "description": "Valutazione dettagliata con esperti per identificare opportunità specifiche",
                "timeline": "Entro 2 settimane",
                "contact": "assessment@enduser-digital.com"
            }
        ]
        
        # Aggiungi step basati su punteggi
        weak_areas = [area for area, score in results.items() if score['percentage'] < 40]
        
        if weak_areas:
            next_steps.append({
                "priority": "high",
                "action": "Piano di miglioramento per aree critiche",
                "description": f"Focus prioritario su: {', '.join([self._get_area_name(area) for area in weak_areas[:2]])}",
                "timeline": "Entro 1 mese"
            })
        
        next_steps.extend([
            {
                "priority": "medium", 
                "action": "Sviluppa piano di formazione digitale",
                "description": "Programma strutturato per migliorare competenze digitali del team",
                "timeline": "Entro 1 mese"
            },
            {
                "priority": "medium",
                "action": "Valuta investimenti in tecnologie prioritarie", 
                "description": "Focus su aree con maggior gap vs benchmark industria",
                "timeline": "Entro 3 mesi"
            }
        ])
        
        return next_steps
    
    def _generate_radar_data(self, results: Dict, benchmark_comparison: Dict) -> List[Dict]:
        """Genera dati per radar chart"""
        radar_data = []
        
        for area_code, score_data in results.items():
            italia_benchmark = benchmark_comparison[area_code]["benchmarks"].get("Italia", {})
            
            radar_data.append({
                "area": self._get_area_name(area_code),
                "area_code": area_code,
                "yourScore": score_data['percentage'],
                "industryAverage": italia_benchmark.get("average_score", 50),
                "maxScore": 100,
                "maturityLevel": score_data['maturity_level'],
                "gap": score_data.get('gap_analysis', 0)
            })
        
        return radar_data
    
    def _calculate_overall_score(self, results: Dict) -> Dict:
        """Calcola punteggio complessivo"""
        if not results:
            return {"overall_percentage": 0, "maturity_level": "beginner"}
        
        total_percentage = sum(score['percentage'] for score in results.values())
        average_percentage = total_percentage / len(results)
        
        return {
            "overall_percentage": round(average_percentage, 2),
            "maturity_level": self._determine_maturity_level(average_percentage),
            "digital_readiness": "ready" if average_percentage >= 60 else "needs_improvement"
        }
    
    def _get_question_text(self, question_id: str) -> str:
        """Ottieni testo domanda da ID (semplificato)"""
        return f"Question text for {question_id}"
    
    def _calculate_question_score(self, question_id: str, response_data: Dict) -> float:
        """Calcola punteggio singola domanda"""
        if response_data.get('type') == 'scale':
            return float(response_data.get('scale_value', 0) * 2)
        elif response_data.get('type') == 'checkbox':
            selected = response_data.get('selected', [])
            if 'invested' in selected or 'implemented' in selected:
                return 10.0
            elif 'planned' in selected:
                return 5.0
        return 0.0
    
    def get_session_results(self, session_id: int) -> Dict:
        """Ottieni risultati sessione esistente"""
        session = self.db.query(AssessmentSession).filter_by(id=session_id).first()
        if not session:
            raise ValueError("Session not found")
        
        results = self.db.query(AssessmentResult).filter_by(session_id=session_id).all()
        
        # Ricostruisci struttura risultati
        results_dict = {}
        for result in results:
            results_dict[result.area_code] = {
                "score": float(result.score),
                "max_score": float(result.max_score),
                "percentage": float(result.percentage),
                "maturity_level": result.maturity_level,
                "benchmark_score": float(result.benchmark_score) if result.benchmark_score else None,
                "gap_analysis": float(result.gap_analysis) if result.gap_analysis else None
            }
        
        recommendations = self._generate_ai_recommendations(results_dict)
        benchmark_comparison = self._get_benchmark_comparison(results_dict)
        
        return {
            "session_id": session_id,
            "company_name": session.company_name,
            "results": results_dict,
            "overall_score": self._calculate_overall_score(results_dict),
            "recommendations": recommendations,
            "benchmark_comparison": benchmark_comparison,
            "next_steps": self._generate_next_steps(results_dict),
            "radar_data": self._generate_radar_data(results_dict, benchmark_comparison),
            "completed_at": session.completed_at.isoformat() if session.completed_at else None
        }
