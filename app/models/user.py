import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)

    profile: Mapped["UserProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    exercises: Mapped[list["Exercise"]] = relationship(back_populates="user")
    workouts: Mapped[list["Workout"]] = relationship(back_populates="user")


class UserProfile(Base):
    __tablename__ = "user_profile"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    timezone: Mapped[str | None] = mapped_column(String(50))
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    height_cm: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))
    gender: Mapped[str | None] = mapped_column(String(10))
    default_unit: Mapped[str] = mapped_column(String(5), server_default="kg")

    user: Mapped["User"] = relationship(back_populates="profile")


# Avoid circular import issues — these are resolved at runtime via string refs
from app.models.exercise import Exercise  # noqa: E402, F401
from app.models.workout import Workout  # noqa: E402, F401
