"""SQLAlchemy ORM models for VeriPost.

PostPackage and PostFile represent the core data model for uploaded
post processor packages and their constituent files stored in MinIO.
"""

import uuid

from sqlalchemy import Column, ForeignKey, Integer, Text, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class PostPackage(Base):
    """A post processor package (one SRC + supporting files)."""

    __tablename__ = "post_packages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    machine_type = Column(Text, nullable=True)
    controller_type = Column(Text, nullable=True)
    platform = Column(Text, nullable=False, default="camworks")
    status = Column(Text, nullable=False, default="pending")
    error_message = Column(Text, nullable=True)
    error_detail = Column(Text, nullable=True)
    file_count = Column(Integer, nullable=True)
    section_count = Column(Integer, nullable=True)
    minio_prefix = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    files = relationship("PostFile", back_populates="package", cascade="all, delete-orphan")


class PostFile(Base):
    """A single file within a post processor package, stored in MinIO."""

    __tablename__ = "post_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    package_id = Column(
        UUID(as_uuid=True),
        ForeignKey("post_packages.id", ondelete="CASCADE"),
        nullable=False,
    )
    filename = Column(Text, nullable=False)
    file_extension = Column(Text, nullable=False)
    minio_key = Column(Text, nullable=False)
    size_bytes = Column(Integer, nullable=True)
    content_hash = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    package = relationship("PostPackage", back_populates="files")
