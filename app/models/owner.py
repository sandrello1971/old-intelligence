from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.core.database import Base

# ✅ Lista di email con privilegi admin
ADMIN_EMAILS = {
    "s.andrello@enduser-italia.com",
    "c.persico@enduser-italia.com",
    "l.vitaletti@enduser-italia.com",
    "l.sala@enduser-italia.com"
}

class Owner(Base):
    __tablename__ = "owners"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    surname = Column(String)
    email = Column(String, unique=True, index=True)

    # Relazione inversa con i Task (task.owner_ref → owner)
    tasks_owned = relationship("Task", back_populates="owner_ref")

    def is_admin(self) -> bool:
        """Restituisce True se l'utente è nella lista degli admin"""
        return self.email in ADMIN_EMAILS
