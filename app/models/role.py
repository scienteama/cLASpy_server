from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base

class Role(Base):
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

    users = relationship("User", back_populates="role")