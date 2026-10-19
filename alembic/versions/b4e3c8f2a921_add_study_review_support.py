"""Add review idempotency and missing study-history tables.

Revision ID: b4e3c8f2a921
Revises: 1f4296c2362e
Create Date: 2026-10-15

"""
from alembic import op
import sqlalchemy as sa


revision = "b4e3c8f2a921"
down_revision = "1f4296c2362e"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "study_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("flashcard_id", sa.Integer(), nullable=False),
        sa.Column("studied_at", sa.DateTime(), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=True),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["flashcard_id"], ["flashcards.id"]),
        mysql_engine="InnoDB",
    )
    op.create_index(
        "uq_study_events_user_request_id",
        "study_events",
        ["user_id", "request_id"],
        unique=True,
    )

    op.create_table(
        "quiz_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=True),
        sa.Column("note_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("question_index", sa.Integer(), nullable=True),
        sa.Column("question_order", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["topic_id"], ["topic.id"]),
        sa.ForeignKeyConstraint(["note_id"], ["notes.id"]),
        mysql_engine="InnoDB",
    )

    op.create_table(
        "quiz_question_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("quiz_attempt_id", sa.Integer(), nullable=False),
        sa.Column("flashcard_id", sa.Integer(), nullable=False),
        sa.Column("user_answer", sa.Text(), nullable=False),
        sa.Column("correct_answer", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("time_taken", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["quiz_attempt_id"], ["quiz_attempts.id"]),
        sa.ForeignKeyConstraint(["flashcard_id"], ["flashcards.id"]),
        mysql_engine="InnoDB",
    )

    # Batch mode preserves rows and rebuilds this table on SQLite, which
    # does not support ALTER COLUMN TYPE. Other databases use normal ALTER.
    with op.batch_alter_table("flashcard_progress") as batch:
        batch.alter_column(
            "progress",
            existing_type=sa.Integer(),
            type_=sa.Float(),
            existing_nullable=True,
        )


def downgrade():
    raise RuntimeError(
        "This migration preserves study and quiz history; restore from a database backup instead of downgrading."
    )
