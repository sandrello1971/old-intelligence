# app/models/hashtag.py
from sqlalchemy import Column, Integer, String
from app.core.database import Base

class Hashtag(Base):
    __tablename__ = "hashtags"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
