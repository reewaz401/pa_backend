"""add is_global column and seed global exercises

Revision ID: 003
Revises: 002
Create Date: 2026-02-21
"""
from typing import Sequence, Union
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

GLOBAL_EXERCISES = [
    # Chest
    ("Bench Press", "Chest", "Barbell"),
    ("Incline Bench Press", "Chest", "Barbell"),
    ("Dumbbell Fly", "Chest", "Dumbbells"),
    ("Cable Crossover", "Chest", "Cable"),
    ("Push-Up", "Chest", "Bodyweight"),
    ("Chest Dip", "Chest", "Bodyweight"),
    # Back
    ("Barbell Row", "Back", "Barbell"),
    ("Lat Pulldown", "Back", "Cable"),
    ("Seated Cable Row", "Back", "Cable"),
    ("Pull-Up", "Back", "Bodyweight"),
    ("T-Bar Row", "Back", "Barbell"),
    ("Face Pull", "Back", "Cable"),
    # Shoulders
    ("Overhead Press", "Shoulders", "Barbell"),
    ("Lateral Raise", "Shoulders", "Dumbbells"),
    ("Front Raise", "Shoulders", "Dumbbells"),
    ("Rear Delt Fly", "Shoulders", "Dumbbells"),
    ("Arnold Press", "Shoulders", "Dumbbells"),
    # Biceps
    ("Barbell Curl", "Biceps", "Barbell"),
    ("Dumbbell Curl", "Biceps", "Dumbbells"),
    ("Hammer Curl", "Biceps", "Dumbbells"),
    ("Preacher Curl", "Biceps", "Barbell"),
    ("Cable Curl", "Biceps", "Cable"),
    # Triceps
    ("Tricep Pushdown", "Triceps", "Cable"),
    ("Skull Crusher", "Triceps", "Barbell"),
    ("Overhead Tricep Extension", "Triceps", "Dumbbells"),
    ("Close-Grip Bench Press", "Triceps", "Barbell"),
    ("Dip", "Triceps", "Bodyweight"),
    # Quads
    ("Squat", "Quads", "Barbell"),
    ("Leg Press", "Quads", "Machine"),
    ("Leg Extension", "Quads", "Machine"),
    ("Front Squat", "Quads", "Barbell"),
    ("Bulgarian Split Squat", "Quads", "Dumbbells"),
    ("Lunges", "Quads", "Dumbbells"),
    # Hamstrings
    ("Romanian Deadlift", "Hamstrings", "Barbell"),
    ("Leg Curl", "Hamstrings", "Machine"),
    ("Good Morning", "Hamstrings", "Barbell"),
    ("Nordic Curl", "Hamstrings", "Bodyweight"),
    # Glutes
    ("Hip Thrust", "Glutes", "Barbell"),
    ("Glute Bridge", "Glutes", "Bodyweight"),
    ("Cable Kickback", "Glutes", "Cable"),
    # Calves
    ("Standing Calf Raise", "Calves", "Machine"),
    ("Seated Calf Raise", "Calves", "Machine"),
    # Core
    ("Plank", "Core", "Bodyweight"),
    ("Hanging Leg Raise", "Core", "Bodyweight"),
    ("Cable Crunch", "Core", "Cable"),
    ("Ab Wheel Rollout", "Core", "Ab Wheel"),
    ("Russian Twist", "Core", "Bodyweight"),
    # Full Body
    ("Deadlift", "Full Body", "Barbell"),
    ("Clean and Press", "Full Body", "Barbell"),
    ("Kettlebell Swing", "Full Body", "Kettlebell"),
]


def upgrade() -> None:
    # Add is_global column
    op.add_column(
        "exercises",
        sa.Column(
            "is_global",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
    )

    # Make user_id nullable
    op.alter_column(
        "exercises",
        "user_id",
        existing_type=sa.dialects.postgresql.UUID(),
        nullable=True,
    )

    # Replace unique constraint with partial unique index
    op.drop_constraint("uq_exercises_user_name", "exercises", type_="unique")
    op.execute(
        "CREATE UNIQUE INDEX uq_exercises_user_name "
        "ON exercises (user_id, name) WHERE user_id IS NOT NULL"
    )

    # Seed global exercises
    exercises_table = sa.table(
        "exercises",
        sa.column("id", sa.dialects.postgresql.UUID()),
        sa.column("name", sa.String()),
        sa.column("muscle_group", sa.String()),
        sa.column("equipment", sa.String()),
        sa.column("is_global", sa.Boolean()),
        sa.column("user_id", sa.dialects.postgresql.UUID()),
    )
    op.bulk_insert(
        exercises_table,
        [
            {
                "id": str(uuid4()),
                "name": name,
                "muscle_group": muscle_group,
                "equipment": equipment,
                "is_global": True,
                "user_id": None,
            }
            for name, muscle_group, equipment in GLOBAL_EXERCISES
        ],
    )


def downgrade() -> None:
    # Remove seeded global exercises
    op.execute("DELETE FROM exercises WHERE is_global = true")

    # Restore original unique constraint
    op.execute("DROP INDEX IF EXISTS uq_exercises_user_name")
    op.create_unique_constraint(
        "uq_exercises_user_name", "exercises", ["user_id", "name"]
    )

    # Make user_id non-nullable again
    op.alter_column(
        "exercises",
        "user_id",
        existing_type=sa.dialects.postgresql.UUID(),
        nullable=False,
    )

    # Drop is_global column
    op.drop_column("exercises", "is_global")
