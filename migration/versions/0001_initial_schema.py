"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "pdf_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("html_content", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    meeting_status = postgresql.ENUM(
        "UPLOADED", "TRANSCRIBING", "SUMMARIZING", "GENERATING_PDF",
        "COMPLETED", "FAILED", name="meeting_status",
    )
    op.create_table(
        "meetings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("language", sa.String(10), server_default="id"),
        sa.Column("storage_path", sa.String(1024), nullable=True),
        sa.Column("status", meeting_status, nullable=False, server_default="UPLOADED"),
        sa.Column("pdf_url", sa.String(1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_meetings_user_id", "meetings", ["user_id"])
    op.create_index("ix_meetings_status", "meetings", ["status"])

    op.create_table(
        "transcriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("meeting_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("meetings.id", ondelete="CASCADE"),
                  nullable=False, unique=True),
        sa.Column("full_text", sa.Text(), nullable=True),
        sa.Column("segments", postgresql.JSONB(), nullable=True),
        sa.Column("language", sa.String(10), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "summaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("meeting_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("meetings.id", ondelete="CASCADE"),
                  nullable=False, unique=True),
        sa.Column("template_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("pdf_templates.id", ondelete="SET NULL"), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("key_points", postgresql.JSONB(), nullable=True),
        sa.Column("action_items", postgresql.JSONB(), nullable=True),
        sa.Column("decisions", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    job_type = postgresql.ENUM(
        "TRANSCRIPTION", "SUMMARIZATION", "PDF_GENERATION", name="job_type",
    )
    job_status = postgresql.ENUM(
        "QUEUED", "RUNNING", "COMPLETED", "FAILED", name="job_status",
    )
    op.create_table(
        "processing_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("meeting_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_type", job_type, nullable=False),
        sa.Column("status", job_status, nullable=False, server_default="QUEUED"),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_processing_jobs_meeting_id", "processing_jobs", ["meeting_id"])
    op.create_index("ix_processing_jobs_celery_task_id", "processing_jobs", ["celery_task_id"])


def downgrade() -> None:
    op.drop_table("processing_jobs")
    op.drop_table("summaries")
    op.drop_table("transcriptions")
    op.drop_table("meetings")
    op.drop_table("pdf_templates")
    op.drop_table("users")
    # Hapus tipe enum (urutan setelah tabel yang memakainya di-drop).
    op.execute("DROP TYPE IF EXISTS job_status")
    op.execute("DROP TYPE IF EXISTS job_type")
    op.execute("DROP TYPE IF EXISTS meeting_status")
