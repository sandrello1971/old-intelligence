"""
Assessment Module Models - Standalone
Data: 2025-06-16
Versione: 1.0 - Fixed metadata mapping
"""

from sqlalchemy import Column, Integer, String, Text, DECIMAL, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.core.database import Base

class AssessmentSession(Base):
    """Sessione assessment con isolamento completo dal core"""
    __tablename__ = "sessions"
    __table_args__ = {'schema': 'assessment'}
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, nullable=False)
    user_id = Column(String, nullable=True)
    session_code = Column(String(50), unique=True, nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    status = Column(String(20), default='draft')
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    session_metadata = Column('metadata', JSONB, default={})  # Mappa a colonna 'metadata'
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())

class AssessmentResult(Base):
    """Risultati assessment per area (M2.1-M2.6)"""
    __tablename__ = "results"
    __table_args__ = {'schema': 'assessment'}
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, nullable=False)
    area_code = Column(String(10), nullable=False, index=True)
    area_name = Column(String(100), nullable=False)
    score = Column(DECIMAL(5, 2), nullable=False, default=0.00)
    max_score = Column(DECIMAL(5, 2), nullable=False, default=0.00)
    percentage = Column(DECIMAL(5, 2), nullable=False, default=0.00)
    maturity_level = Column(String(20), nullable=False)
    benchmark_score = Column(DECIMAL(5, 2), nullable=True)
    gap_analysis = Column(DECIMAL(5, 2), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class AssessmentResponse(Base):
    """Risposte dettagliate alle domande assessment"""
    __tablename__ = "responses"
    __table_args__ = {'schema': 'assessment'}
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, nullable=False)
    question_id = Column(String(50), nullable=False)
    question_text = Column(Text, nullable=False)
    area_code = Column(String(10), nullable=False, index=True)
    answer_type = Column(String(20), nullable=False)
    selected_values = Column(JSONB, nullable=False, default=[])
    score = Column(DECIMAL(5, 2), nullable=False, default=0.00)
    created_at = Column(DateTime, server_default=func.now())

class AssessmentBenchmarkData(Base):
    """Dati benchmark industria italiana"""
    __tablename__ = "benchmark_data"
    __table_args__ = {'schema': 'assessment'}
    
    id = Column(Integer, primary_key=True, index=True)
    industry = Column(String(100), nullable=False)
    company_size = Column(String(50), default='all')
    area_code = Column(String(10), nullable=False)
    area_name = Column(String(100), nullable=False)
    average_score = Column(DECIMAL(5, 2), nullable=False)
    percentile_25 = Column(DECIMAL(5, 2), nullable=False)
    percentile_50 = Column(DECIMAL(5, 2), nullable=False)
    percentile_75 = Column(DECIMAL(5, 2), nullable=False)
    sample_size = Column(Integer, nullable=False, default=0)
    data_source = Column(String(100), default='ISTAT 2024')
    last_updated = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())
