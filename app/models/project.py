from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from app.database import Base
from sqlalchemy.orm import relationship

class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    team = relationship("ProjectTeam", back_populates="project", overlaps="members")
    members = relationship("User", secondary="project_team", back_populates="projects", overlaps="team")

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}')>"


class ProjectTeam(Base):
    __tablename__ = 'project_team'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_user"),
        Index("ix_project_user", "project_id", "user_id"),
    )

    project = relationship("Project", back_populates="team", overlaps="members,projects")
    user = relationship("User", back_populates="team", overlaps="projects,team")
    role = relationship("Role")

    def __repr__(self):
        return f"<ProjectTeam(project_id={self.project_id}, user_id={self.user_id}, role_id={self.role_id})>"