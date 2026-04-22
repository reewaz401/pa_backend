"""create workout_logs table

Revision ID: 007
Revises: 006
Create Date: 2026-02-21
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "workout_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workout_id", UUID(as_uuid=True), sa.ForeignKey("workouts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("exercise_id", UUID(as_uuid=True), sa.ForeignKey("exercises.id", ondelete="SET NULL"), nullable=True),
        sa.Column("exercise_name", sa.String(200), nullable=False),
        sa.Column("muscle_group", sa.String(100), nullable=True),
        sa.Column("equipment", sa.String(100), nullable=True),
        sa.Column("day", sa.SmallInteger, nullable=True),
        sa.Column("workout_date", sa.Date, nullable=False),
        sa.Column("sets_data", sa.JSON, nullable=False),
        sa.Column("total_calories", sa.Numeric(7, 2), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_workout_logs_user_id", "workout_logs", ["user_id"])
    op.create_index("ix_workout_logs_exercise_id", "workout_logs", ["exercise_id"])
    op.create_index("ix_workout_logs_workout_date", "workout_logs", ["workout_date"])


def downgrade() -> None:
    op.drop_index("ix_workout_logs_workout_date")
    op.drop_index("ix_workout_logs_exercise_id")
    op.drop_index("ix_workout_logs_user_id")
    op.drop_table("workout_logs")
