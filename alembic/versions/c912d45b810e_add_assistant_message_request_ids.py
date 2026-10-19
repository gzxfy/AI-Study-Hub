"""Add idempotency keys to assistant user messages.

Revision ID: c912d45b810e
Revises: b4e3c8f2a921
Create Date: 2026-10-18

"""
from alembic import op
import sqlalchemy as sa


revision = "c912d45b810e"
down_revision = "b4e3c8f2a921"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("messages", sa.Column("request_id", sa.String(length=128), nullable=True))
    op.create_index(
        "uq_messages_conversation_request_id",
        "messages",
        ["conversation_id", "request_id"],
        unique=True,
    )


def downgrade():
    op.drop_index("uq_messages_conversation_request_id", table_name="messages")
    op.drop_column("messages", "request_id")