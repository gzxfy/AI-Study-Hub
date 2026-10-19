"""add pdf path and study plan tables

Revision ID: 8e7b3d2a1c44
Revises: caa005233e4d
Create Date: 2026-07-20 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8e7b3d2a1c44"
down_revision = "caa005233e4d"
branch_labels = None
depends_on = None


def upgrade():
    # Keep the existing notes table in sync with the current Note model.
    op.add_column(
        "notes",
        sa.Column("uploaded_pdf_path", sa.String(length=500), nullable=True),
    )

    # These tables support the AI study-plan feature already present in the models.
    op.create_table(
        "study_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("start_date", sa.DateTime(), nullable=False),
        sa.Column("end_date", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "study_plan_days",
        sa.Column("study_plan_id", sa.Integer(), nullable=False),
        sa.Column("day_number", sa.Integer(), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("task_json", sa.JSON(), nullable=True),
        sa.Column("estimated_time_minutes", sa.Integer(), nullable=True),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["study_plan_id"], ["study_plans.id"]),
        sa.PrimaryKeyConstraint("study_plan_id", "day_number"),
    )

    op.create_table(
        "study_plan_progress",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("study_plan_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("completed_days", sa.Integer(), nullable=True),
        sa.Column("total_days", sa.Integer(), nullable=True),
        sa.Column("last_updated", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["study_plan_id"], ["study_plans.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("study_plan_progress")
    op.drop_table("study_plan_days")
    op.drop_table("study_plans")
    op.drop_column("notes", "uploaded_pdf_path")