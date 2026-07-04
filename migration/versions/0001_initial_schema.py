"""initial schema (integer PK, enum dari schemas/common)

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# PK: BIGINT di Postgres, INTEGER di SQLite (agar auto-increment jalan lintas-DB)
PK = sa.BigInteger().with_variant(sa.Integer(), "sqlite")
# JSON: JSONB di Postgres, JSON biasa di DB lain
JSONB = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")

processing_status = sa.Enum(
    "uploaded", "queued", "transcribing", "summarizing",
    "generating_pdf", "completed", "failed",
    name="processing_status",
)
job_type = sa.Enum(
    "transcription", "summarization", "pdf_generation", name="job_type",
)
job_status = sa.Enum(
    "pending", "started", "progress", "success", "failure", "retry", "revoked",
    name="job_status",
)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", PK, primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "pdf_templates",
        sa.Column("id", PK, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("html_content", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "meetings",
        sa.Column("id", PK, primary_key=True, autoincrement=True),
        sa.Column("user_id", PK, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("language", sa.String(10), server_default="id"),
        sa.Column("storage_path", sa.String(1024), nullable=True),
        sa.Column("storage_bucket", sa.String(255), nullable=True),
        sa.Column("status", processing_status, nullable=False, server_default="uploaded"),
        sa.Column("pdf_url", sa.String(1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_meetings_user_id", "meetings", ["user_id"])
    op.create_index("ix_meetings_status", "meetings", ["status"])

    op.create_table(
        "transcriptions",
        sa.Column("id", PK, primary_key=True, autoincrement=True),
        sa.Column("meeting_id", PK, sa.ForeignKey("meetings.id", ondelete="CASCADE"),
                  nullable=False, unique=True),
        sa.Column("full_text", sa.Text(), nullable=True),
        sa.Column("segments", JSONB, nullable=True),
        sa.Column("language", sa.String(10), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "summaries",
        sa.Column("id", PK, primary_key=True, autoincrement=True),
        sa.Column("meeting_id", PK, sa.ForeignKey("meetings.id", ondelete="CASCADE"),
                  nullable=False, unique=True),
        sa.Column("template_id", PK, sa.ForeignKey("pdf_templates.id", ondelete="SET NULL"),
                  nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("key_points", JSONB, nullable=True),
        sa.Column("action_items", JSONB, nullable=True),
        sa.Column("decisions", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "processing_jobs",
        sa.Column("id", PK, primary_key=True, autoincrement=True),
        sa.Column("meeting_id", PK, sa.ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_type", job_type, nullable=False),
        sa.Column("status", job_status, nullable=False, server_default="pending"),
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
    # hapus tipe enum (khusus Postgres)
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for enum_name in ("job_status", "job_type", "processing_status"):
            op.execute(f"DROP TYPE IF EXISTS {enum_name}")
