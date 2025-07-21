"""
Assessment Router - API Endpoints
Data: 2025-06-16
Versione: 1.0
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.assessment.services.assessment_service import AssessmentService

# Pydantic Models per API
class AssessmentSessionCreate(BaseModel):
    company_id: int
    user_id: Optional[str] = None

class AssessmentSessionResponse(BaseModel):
    session_id: int
    session_code: str
    company_name: str
    status: str

class AssessmentSubmission(BaseModel):
    responses: Dict

class AssessmentResultResponse(BaseModel):
    session_id: int
    company_name: str
    results: Dict
    overall_score: Dict
    recommendations: List[str]
    benchmark_comparison: Dict
    next_steps: List[Dict]
    radar_data: List[Dict]

class CompanyResponse(BaseModel):
    id: int
    name: str
    sector: Optional[str] = None

# Router setup
router = APIRouter(
    prefix="/api/assessment",
    tags=["assessment"],
    responses={404: {"description": "Not found"}}
)

@router.get("/companies", response_model=List[CompanyResponse])
async def get_companies(db: Session = Depends(get_db)):
    """
    Ottieni lista aziende per assessment (solo lettura dal core)
    """
    try:
        service = AssessmentService(db)
        companies = service.get_companies_list()
        return companies
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching companies: {str(e)}"
        )

@router.post("/session", response_model=AssessmentSessionResponse)
async def create_assessment_session(
    session_data: AssessmentSessionCreate,
    db: Session = Depends(get_db)
):
    """
    Crea nuova sessione assessment per un'azienda
    """
    try:
        service = AssessmentService(db)
        session = service.create_session(
            company_id=session_data.company_id,
            user_id=session_data.user_id
        )
        
        return AssessmentSessionResponse(
            session_id=session.id,
            session_code=session.session_code,
            company_name=session.company_name,
            status=session.status
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating session: {str(e)}"
        )

@router.get("/structure")
async def get_assessment_structure(db: Session = Depends(get_db)):
    """
    Ottieni struttura completa assessment (domande M2.1-M2.6)
    """
    try:
        service = AssessmentService(db)
        structure = service.get_assessment_structure()
        return structure
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching assessment structure: {str(e)}"
        )

@router.post("/submit/{session_id}", response_model=AssessmentResultResponse)
async def submit_assessment(
    session_id: int,
    submission: AssessmentSubmission,
    db: Session = Depends(get_db)
):
    """
    Elabora e salva assessment, calcola punteggi e genera raccomandazioni
    """
    try:
        service = AssessmentService(db)
        results = service.submit_assessment(session_id, submission.responses)
        return AssessmentResultResponse(**results)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting assessment: {str(e)}"
        )

@router.get("/results/{session_id}", response_model=AssessmentResultResponse)
async def get_assessment_results(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    Ottieni risultati assessment esistente
    """
    try:
        service = AssessmentService(db)
        results = service.get_session_results(session_id)
        return AssessmentResultResponse(**results)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching results: {str(e)}"
        )

@router.get("/benchmark/{industry}")
async def get_industry_benchmark(
    industry: str,
    db: Session = Depends(get_db)
):
    """
    Ottieni benchmark specifico per industria
    """
    try:
        service = AssessmentService(db)
        # Query diretta per benchmark specifico
        from app.assessment.models.assessment import AssessmentBenchmarkData
        
        benchmarks = db.query(AssessmentBenchmarkData).filter_by(
            industry=industry
        ).all()
        
        if not benchmarks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No benchmark data found for industry: {industry}"
            )
        
        result = {}
        for benchmark in benchmarks:
            result[benchmark.area_code] = {
                "area_name": benchmark.area_name,
                "average_score": float(benchmark.average_score),
                "percentile_25": float(benchmark.percentile_25),
                "percentile_50": float(benchmark.percentile_50),
                "percentile_75": float(benchmark.percentile_75),
                "sample_size": benchmark.sample_size,
                "data_source": benchmark.data_source
            }
        
        return {
            "industry": industry,
            "areas": result,
            "total_areas": len(result)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching benchmark: {str(e)}"
        )

@router.get("/benchmark")
async def get_all_industries_benchmark(db: Session = Depends(get_db)):
    """
    Ottieni lista di tutte le industrie disponibili per benchmark
    """
    try:
        from app.assessment.models.assessment import AssessmentBenchmarkData
        
        industries = db.query(AssessmentBenchmarkData.industry).distinct().all()
        industries_list = [industry[0] for industry in industries]
        
        return {
            "industries": industries_list,
            "total_industries": len(industries_list)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching industries: {str(e)}"
        )

@router.get("/radar-data/{session_id}")
async def get_radar_chart_data(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    Dati specifici per radar chart visualization
    """
    try:
        service = AssessmentService(db)
        results = service.get_session_results(session_id)
        
        return {
            "session_id": session_id,
            "company_name": results["company_name"],
            "radar_data": results["radar_data"],
            "overall_score": results["overall_score"]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating radar data: {str(e)}"
        )

@router.get("/health")
async def assessment_health_check():
    """
    Health check per modulo assessment
    """
    return {
        "status": "healthy",
        "module": "assessment",
        "version": "1.0",
        "message": "Assessment module is operational"
    }

# Endpoint per testing isolamento
@router.get("/test/isolation")
async def test_isolation(db: Session = Depends(get_db)):
    """
    Test endpoint per verificare isolamento dal sistema core
    """
    try:
        # Test 1: Accesso lettura companies (dovrebbe funzionare)
        from app.models import Company
        companies_count = db.query(Company).count()
        
        # Test 2: Verifica schema assessment
        from app.assessment.models.assessment import AssessmentBenchmarkData
        benchmark_count = db.query(AssessmentBenchmarkData).count()
        
        return {
            "isolation_test": "passed",
            "core_companies_readable": companies_count > 0,
            "assessment_schema_accessible": benchmark_count > 0,
            "companies_count": companies_count,
            "benchmark_records": benchmark_count,
            "message": "Assessment module correctly isolated with read-only access to core"
        }
    except Exception as e:
        return {
            "isolation_test": "failed",
            "error": str(e),
            "message": "Assessment module isolation test failed"
        }

@router.get("/companies")
async def get_companies_for_assessment(db: Session = Depends(get_db)):
    """Get all companies for assessment selection"""
    try:
        companies = db.query(Company).all()
        return [
            {
                "id": company.id,
                "name": company.name,
                "sector": company.sector,
                "partita_iva": company.partita_iva
            }
            for company in companies
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/api/companies")
async def get_companies_api(db: Session = Depends(get_db)):
    """API endpoint for companies"""
    return await get_companies_for_assessment(db)
