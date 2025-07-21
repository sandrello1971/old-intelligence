from sqlalchemy import Column, Integer, String
from app.core.database import Base

class SubType(Base):
    __tablename__ = "sub_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False)
