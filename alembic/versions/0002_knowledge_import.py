"""Governed knowledge records and import batches.

Revision ID: 0002
Revises: 0001
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _common_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "knowledge_import_batches", *_common_columns(),
        sa.Column("batch_key", sa.String(64), nullable=False),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("actor", sa.String(120), nullable=False),
        sa.Column("counts", sa.JSON(), nullable=False),
        sa.Column("errors", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("batch_key"),
    )
    op.create_table(
        "knowledge_cases", *_common_columns(),
        sa.Column("external_case_id", sa.String(80), nullable=False),
        sa.Column("source_chat", sa.String(240), nullable=False),
        sa.Column("knowledge_tier", sa.String(80), nullable=False),
        sa.Column("source_validation", sa.String(160), nullable=False),
        sa.Column("technical_access", sa.String(40), nullable=False),
        sa.Column("domain", sa.String(160), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("external_case_id"),
    )
    op.create_table(
        "knowledge_contents", *_common_columns(),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("byte_size", sa.BigInteger(), nullable=False),
        sa.Column("canonical_path", sa.Text(), nullable=False),
        sa.Column("source_format", sa.String(40), nullable=False),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("sha256"),
    )
    op.create_table(
        "knowledge_attachments", *_common_columns(),
        sa.Column("content_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=True),
        sa.Column("relative_path", sa.Text(), nullable=False),
        sa.Column("import_tier", sa.String(80), nullable=False),
        sa.Column("technical_access", sa.String(40), nullable=False),
        sa.Column("source_format", sa.String(40), nullable=False),
        sa.ForeignKeyConstraint(["content_id"], ["knowledge_contents.id"]),
        sa.ForeignKeyConstraint(["case_id"], ["knowledge_cases.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("relative_path", name="uq_knowledge_attachment_path"),
    )
    op.create_table(
        "knowledge_documents", *_common_columns(),
        sa.Column("external_document_id", sa.String(80), nullable=False),
        sa.Column("content_id", sa.Uuid(), nullable=True),
        sa.Column("relative_path", sa.Text(), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("knowledge_tier", sa.String(80), nullable=False),
        sa.Column("document_status", sa.String(40), nullable=False),
        sa.Column("technical_access", sa.String(40), nullable=False),
        sa.Column("authoritative", sa.Boolean(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["content_id"], ["knowledge_contents.id"]),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("external_document_id"),
    )
    op.create_table(
        "knowledge_product_scopes", *_common_columns(),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("model_name", sa.String(200), nullable=True),
        sa.Column("voltage_v", sa.String(40), nullable=True),
        sa.Column("serial_number", sa.String(120), nullable=True),
        sa.Column("hardware_revision", sa.String(120), nullable=True),
        sa.Column("software_revision", sa.String(120), nullable=True),
        sa.Column("match_status", sa.String(40), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["knowledge_cases.id"]),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("case_id"),
    )
    op.create_table(
        "knowledge_audio_transcripts", *_common_columns(),
        sa.Column("audio_id", sa.String(80), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("transcript_path", sa.Text(), nullable=False),
        sa.Column("language", sa.String(20), nullable=False),
        sa.Column("transcript_status", sa.String(60), nullable=False),
        sa.Column("authoritative", sa.Boolean(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["knowledge_cases.id"]),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("audio_id"),
    )


def downgrade() -> None:
    op.drop_table("knowledge_audio_transcripts")
    op.drop_table("knowledge_product_scopes")
    op.drop_table("knowledge_documents")
    op.drop_table("knowledge_attachments")
    op.drop_table("knowledge_contents")
    op.drop_table("knowledge_cases")
    op.drop_table("knowledge_import_batches")
