from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base
from .role import Role

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    firstname = Column(String, nullable=False)
    lastname = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    last_login = Column(DateTime)
    role_id = Column(Integer, ForeignKey("roles.id"))

    role = relationship("Role", back_populates="users")


    team = relationship("ProjectTeam", back_populates="user", overlaps="projects")
    projects = relationship("Project", secondary="project_team", back_populates="members", overlaps="team")

    def __repr__(self):
        return f"<User(id={self.id}, firstname='{self.firstname}', lastname='{self.lastname}', role_id={self.role_id})>"