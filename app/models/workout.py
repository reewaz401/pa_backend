import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Workout(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "workouts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    workout_date: Mapped[date] = mapped_column(Date, nullable=False)
    day: Mapped[int | None] = mapped_column(SmallInteger)
    title: Mapped[str | None] = mapped_column(String(200))
    notes: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_minutes: Mapped[int | None] = mapped_column(SmallInteger)
    intensity: Mapped[int | None] = mapped_column(SmallInteger)
    calories_est_total: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))

    user: Mapped["User"] = relationship(back_populates="workouts")
    workout_exercises: Mapped[list["WorkoutExercise"]] = relationship(
        back_populates="workout", cascade="all, delete-orphan", order_by="WorkoutExercise.order_index"
    )


class WorkoutExercise(UUIDMixin, Base):
    __tablename__ = "workout_exercises"

    workout_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False
    )
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exercises.id"), nullable=False
    )
    order_index: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    calories_est: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    notes: Mapped[str | None] = mapped_column(Text)

    workout: Mapped["Workout"] = relationship(back_populates="workout_exercises")
    exercise: Mapped["Exercise"] = relationship()
    sets: Mapped[list["Set"]] = relationship(
        back_populates="workout_exercise", cascade="all, delete-orphan", order_by="Set.set_index"
    )


from app.models.exercise import Exercise  # noqa: E402, F401
from app.models.set import Set  # noqa: E402, F401
from app.models.user import User  # noqa: E402, F401
