from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base


class RecoveryCode(Base):
    __tablename__ = "recovery_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code_hash = Column(String(255), nullable=False, unique=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    used_at = Column(DateTime(timezone=True), nullable=True, default=None)
    expires_at = Column(DateTime(timezone=True), nullable=True, default=None)

    # Relations
    user = relationship("User", back_populates="recovery_codes")

    __table_args__ = (Index("idx_recovery_user_active", "user_id", "used_at"),)
