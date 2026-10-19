"""Bring migrated study plans into line with the existing model.

Revision ID: d8a17c09e452
Revises: c912d45b810e
"""
from alembic import op
import sqlalchemy as sa


revision = "d8a17c09e452"
down_revision = "c912d45b810e"
branch_labels = None
depends_on = None


def upgrade():
    # Older migration-built databases lack this column. Some development
    # databases were created from the models and already have it.
    columns = sa.inspect(op.get_bind()).get_columns("study_plans")
    if not any(column["name"] == "completed" for column in columns):
        op.add_column(
            "study_plans",
            sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        )


def downgrade():
    raise RuntimeError("Restore a database backup instead of dropping study-plan data.")
