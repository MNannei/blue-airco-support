"""Initial ticket, safety, audit, and webhook schema.

Revision ID: 0001
Revises: None
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0001"
down_revision: str | None = None
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
        "users",
        *_common_columns(),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "customers",
        *_common_columns(),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "contacts",
        *_common_columns(),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("value", sa.String(length=320), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "vessels",
        *_common_columns(),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "product_units",
        *_common_columns(),
        sa.Column("vessel_id", sa.Uuid(), nullable=True),
        sa.Column("serial_number", sa.String(length=120), nullable=False),
        sa.Column("model_name", sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(["vessel_id"], ["vessels.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("serial_number"),
    )
    op.create_table(
        "tickets",
        *_common_columns(),
        sa.Column("customer_id", sa.Uuid(), nullable=True),
        sa.Column("product_unit_id", sa.Uuid(), nullable=True),
        sa.Column("subject", sa.String(length=240), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["product_unit_id"], ["product_units.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "messages",
        *_common_columns(),
        sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("external_message_id", sa.String(length=240), nullable=False),
        sa.Column("direction", sa.String(length=20), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_message_id", name="uq_messages_external_message_id"),
    )
    op.create_table(
        "safety_assessments",
        *_common_columns(),
        sa.Column("ticket_id", sa.Uuid(), nullable=True),
        sa.Column("message_id", sa.Uuid(), nullable=True),
        sa.Column("risk_level", sa.String(length=40), nullable=False),
        sa.Column("requires_human_review", sa.Boolean(), nullable=False),
        sa.Column("workflow_blocked", sa.Boolean(), nullable=False),
        sa.Column("anonymized_input", sa.Text(), nullable=False),
        sa.Column("trigger_reasons", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"]),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "audit_events",
        *_common_columns(),
        sa.Column("ticket_id", sa.Uuid(), nullable=True),
        sa.Column("safety_assessment_id", sa.Uuid(), nullable=True),
        sa.Column("actor_type", sa.String(length=40), nullable=False),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["safety_assessment_id"], ["safety_assessments.id"]),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "webhook_events",
        *_common_columns(),
        sa.Column("external_message_id", sa.String(length=240), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_message_id", name="uq_webhook_external_message_id"),
    )


def downgrade() -> None:
    op.drop_table("webhook_events")
    op.drop_table("audit_events")
    op.drop_table("safety_assessments")
    op.drop_table("messages")
    op.drop_table("tickets")
    op.drop_table("product_units")
    op.drop_table("vessels")
    op.drop_table("contacts")
    op.drop_table("customers")
    op.drop_table("users")
