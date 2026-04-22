"""add height_cm and gender to user_profile

Revision ID: 005
Revises: 004
Create Date: 2026-02-21
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_profile", sa.Column("height_cm", sa.Numeric(5, 1), nullable=True))
    op.add_column("user_profile", sa.Column("gender", sa.String(10), nullable=True))


def downgrade() -> None:
    op.drop_column("user_profile", "gender")
    op.drop_column("user_profile", "height_cm")
