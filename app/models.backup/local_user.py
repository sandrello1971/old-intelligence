from sqlalchemy import Column, Integer, String, Boolean
from app.core.database import Base

class LocalUser(Base):
    __tablename__ = "local_users"

    id = Column(String, primary_key=True)  # se usi VARCHAR da users
    email = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String, default="user")
    must_change_password = Column(Boolean, default=True)
