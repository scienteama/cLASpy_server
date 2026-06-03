from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String
from app.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    type = Column(String(50), nullable=False)
    message = Column(String(255), nullable=False)
    is_read = Column(Boolean, nullable=False, default=False)

    created_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index(
            "idx_notifications_user_created",
            "user_id",
            "created_at",
        ),
    )
