from sqlalchemy import Column, String, Boolean, BigInteger, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base

class File(Base):
    __tablename__ = "files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)

    parent_id = Column(UUID(as_uuid=True), ForeignKey("files.id"), nullable=True)
    parent = relationship("File", remote_side=[id])

    logical_name = Column(String, nullable=False)
    is_directory = Column(Boolean, default=False)

    hash = Column(String(128), nullable=True)  # plus de unique ici
    mime_type = Column(String, nullable=True)
    size_bytes = Column(BigInteger, nullable=True)
    status = Column(String, default="active")  # active | deleted

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

    # ------------------------
    # Index partiel pour unicité conditionnelle sur fichiers uniquement
    # ------------------------
    __table_args__ = (
        Index(
            "ix_unique_active_file_per_user_folder",
            "user_id",
            "hash",
            "logical_name",
            unique=True,
            postgresql_where=(
                (status == "active") & (is_directory == False)
            ),
        ),
    )
