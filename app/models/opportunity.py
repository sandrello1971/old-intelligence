
from sqlalchemy import Column, Integer, String
from app.core.database import Base
from sqlalchemy.orm import relationship

class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    titolo = Column(String, nullable=True)
    cliente = Column(String, nullable=True)
    descrizione = Column(String, nullable=True)
    stato = Column(String, nullable=True)
    fase = Column(String, nullable=True)
    probabilita = Column(String, nullable=True)
    data_chiusura = Column(String, nullable=True)
    data_creazione = Column(String, nullable=True)
    data_modifica = Column(String, nullable=True)
    proprietario = Column(String, nullable=True)
    commerciale = Column(String, nullable=True)
    codice = Column(String, nullable=True)
    categoria = Column(String, nullable=True)
    ammontare = Column(String, nullable=True)
    activities = relationship("Activity", back_populates="opportunity")

