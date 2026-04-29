from sqlalchemy import Column, String, Boolean, BigInteger, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import hashlib
from app.database import Base


class File(Base):
    __tablename__ = "files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)

    parent_id = Column(UUID(as_uuid=True), ForeignKey("files.id"), nullable=True)
    parent = relationship("File", remote_side=[id])

    logical_name = Column(String, nullable=False)
    is_directory = Column(Boolean, default=False)

    mime_type = Column(String, nullable=True)
    size_bytes = Column(BigInteger, nullable=True)

    status = Column(String, default="active")  # active | deleted | missing

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(
            timezone=True), nullable=False, default=lambda: datetime.now(
            timezone.utc), onupdate=lambda: datetime.now(
                timezone.utc))

    # ------------------------
    # User-specific storage bucket
    # ------------------------
    storage_bucket = Column(
        String(16),
        nullable=False,
        default=lambda context: hashlib.sha1(
            str(context.get_current_parameters()['user_id']).encode()
        ).hexdigest()[:8]
    )

    # ------------------------
    # Unicity index for active entries only
    # ------------------------
    __table_args__ = (
        Index(
            "ix_unique_active_entry_per_folder",
            "parent_id",
            "logical_name",
            unique=True,
            postgresql_where=(status == "active"),
        ),
    )
