"""Create flashcards before their progress and study-history tables.

Revision ID: 0a6f912e7b30
Revises: 8e7b3d2a1c44
"""
from alembic import op
import sqlalchemy as sa


revision = "0a6f912e7b30"
down_revision = "8e7b3d2a1c44"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "flashcards",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("topic_id", sa.Integer(), sa.ForeignKey("topic.id"), nullable=True),
        sa.Column("note_id", sa.Integer(), sa.ForeignKey("notes.id"), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        mysql_engine="InnoDB",
    )


def downgrade():
    op.drop_table("flashcards")
