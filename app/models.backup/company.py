from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.core.database import Base
from sqlalchemy.orm import Session

class Company(Base):
    __tablename__ = "companies"

    id = Column(String, primary_key=True, index=True)
    nome = Column(String, nullable=True)
    partita_iva = Column(String, nullable=True)
    address = Column(String, nullable=True)
    sector = Column(String, nullable=True)
