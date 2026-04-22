"""add calories_est to workout_exercises

Revision ID: 008
Revises: 007
Create Date: 2026-02-21
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("workout_exercises", sa.Column("calories_est", sa.Numeric(7, 2), nullable=True))


def downgrade() -> None:
    op.drop_column("workout_exercises", "calories_est")
