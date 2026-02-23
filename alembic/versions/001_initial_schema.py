"""Initial schema: post_packages and post_files tables with pgvector extension.

Revision ID: 001
Revises: None
Create Date: 2026-02-23
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension (pre-installed in pgvector/pgvector:pg16 image)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "post_packages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("machine_type", sa.Text, nullable=True),
        sa.Column("controller_type", sa.Text, nullable=True),
        sa.Column("platform", sa.Text, nullable=False, server_default="camworks"),
        sa.Column("status", sa.Text, nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("error_detail", sa.Text, nullable=True),
        sa.Column("file_count", sa.Integer, nullable=True),
        sa.Column("section_count", sa.Integer, nullable=True),
        sa.Column("minio_prefix", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "post_files",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "package_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("post_packages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("filename", sa.Text, nullable=False),
        sa.Column("file_extension", sa.Text, nullable=False),
        sa.Column("minio_key", sa.Text, nullable=False),
        sa.Column("size_bytes", sa.Integer, nullable=True),
        sa.Column("content_hash", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # Index for efficient package-file lookups
    op.create_index("ix_post_files_package_id", "post_files", ["package_id"])


def downgrade() -> None:
    op.drop_index("ix_post_files_package_id", table_name="post_files")
    op.drop_table("post_files")
    op.drop_table("post_packages")
    op.execute("DROP EXTENSION IF EXISTS vector")
