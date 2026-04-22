import uuid
from datetime import date, datetime

from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, JSON, Numeric, SmallInteger, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class WorkoutLog(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "workout_logs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    workout_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workouts.id", ondelete="SET NULL"), nullable=True
    )
    exercise_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exercises.id", ondelete="SET NULL"), nullable=True
    )
    exercise_name: Mapped[str] = mapped_column(String(200), nullable=False)
    muscle_group: Mapped[str | None] = mapped_column(String(100))
    equipment: Mapped[str | None] = mapped_column(String(100))
    day: Mapped[int | None] = mapped_column(SmallInteger)
    workout_date: Mapped[date] = mapped_column(Date, nullable=False)
    sets_data: Mapped[list] = mapped_column(JSON, nullable=False)
    total_calories: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
