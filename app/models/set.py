import uuid
from decimal import Decimal

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, SmallInteger, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin


class Set(UUIDMixin, Base):
    __tablename__ = "sets"

    workout_exercise_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workout_exercises.id", ondelete="CASCADE"),
        nullable=False,
    )
    set_index: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    reps: Mapped[int | None] = mapped_column(SmallInteger)
    weight: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    unit: Mapped[str] = mapped_column(String(5), server_default="kg")
    is_warmup: Mapped[bool] = mapped_column(Boolean, server_default="false")
    rpe: Mapped[Decimal | None] = mapped_column(Numeric(3, 1))
    rest_seconds: Mapped[int | None] = mapped_column(SmallInteger)
    calories_est: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    workout_exercise: Mapped["WorkoutExercise"] = relationship(back_populates="sets")


from app.models.workout import WorkoutExercise  # noqa: E402, F401
