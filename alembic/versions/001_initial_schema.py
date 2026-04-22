"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-02-21
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # pgvector — skip if not installed
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT 1 FROM pg_available_extensions WHERE name = 'vector'")
    )
    if result.scalar():
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), unique=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "user_profile",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("timezone", sa.String(50)),
        sa.Column("weight_kg", sa.Numeric(5, 2)),
        sa.Column("default_unit", sa.String(5), server_default="kg"),
    )

    op.create_table(
        "exercises",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("equipment", sa.String(100)),
        sa.Column("muscle_group", sa.String(100)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("user_id", "name", name="uq_exercises_user_name"),
    )
    op.create_index("ix_exercises_user_id", "exercises", ["user_id"])

    op.create_table(
        "workouts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("workout_date", sa.Date, nullable=False),
        sa.Column("title", sa.String(200)),
        sa.Column("notes", sa.Text),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("duration_minutes", sa.SmallInteger),
        sa.Column("intensity", sa.SmallInteger),
        sa.Column("calories_est_total", sa.Numeric(7, 2)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_workouts_user_id", "workouts", ["user_id"])
    op.create_index("ix_workouts_workout_date", "workouts", ["workout_date"])

    op.create_table(
        "workout_exercises",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workout_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workouts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "exercise_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("exercises.id"),
            nullable=False,
        ),
        sa.Column("order_index", sa.SmallInteger, nullable=False, server_default="0"),
        sa.Column("notes", sa.Text),
    )
    op.create_index("ix_workout_exercises_workout_id", "workout_exercises", ["workout_id"])

    op.create_table(
        "sets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workout_exercise_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workout_exercises.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("set_index", sa.SmallInteger, nullable=False, server_default="0"),
        sa.Column("reps", sa.SmallInteger),
        sa.Column("weight", sa.Numeric(6, 2)),
        sa.Column("unit", sa.String(5), server_default="kg"),
        sa.Column("is_warmup", sa.Boolean, server_default="false"),
        sa.Column("rpe", sa.Numeric(3, 1)),
        sa.Column("rest_seconds", sa.SmallInteger),
        sa.Column("calories_est", sa.Numeric(6, 2)),
    )
    op.create_index("ix_sets_workout_exercise_id", "sets", ["workout_exercise_id"])


def downgrade() -> None:
    op.drop_table("sets")
    op.drop_table("workout_exercises")
    op.drop_table("workouts")
    op.drop_table("exercises")
    op.drop_table("user_profile")
    op.drop_table("users")
    op.execute("DROP EXTENSION IF EXISTS vector")
