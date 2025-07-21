from sqlalchemy import Column, Integer, String, Text, DateTime, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Contact(Base):
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    business_card_id = Column(String)
    nome = Column(String, nullable=False)
    cognome = Column(String, nullable=False)
    azienda = Column(String)
    posizione = Column(String)
    telefono = Column(String)
    cellulare = Column(String)
    email = Column(String, index=True)
    sito_web = Column(String)
    indirizzo = Column(Text)
    citta = Column(String)
    cap = Column(String)
    paese = Column(String)
    linkedin = Column(String)
    note = Column(Text)
    tags = Column(ARRAY(Text))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(255))
