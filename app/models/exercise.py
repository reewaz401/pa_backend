import uuid

from sqlalchemy import Boolean, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Exercise(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "exercises"
    __table_args__ = (
        Index(
            "uq_exercises_user_name",
            "user_id",
            "name",
            unique=True,
            postgresql_where=text("user_id IS NOT NULL"),
        ),
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    equipment: Mapped[str | None] = mapped_column(String(100))
    muscle_group: Mapped[str | None] = mapped_column(String(100))
    is_global: Mapped[bool] = mapped_column(
        Boolean, server_default="false", nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="exercises")


from app.models.user import User  # noqa: E402, F401
