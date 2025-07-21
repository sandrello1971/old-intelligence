from sqlalchemy import Column, Integer, String, Boolean, Text
from app.core.database import Base

class SubType(Base):
    __tablename__ = "sub_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False)
    description = Column(Text, nullable=True)  # 🆕 AGGIUNTO
    is_commessa = Column(Boolean, default=False)
    commessa_associata = Column(String(10), nullable=True)
