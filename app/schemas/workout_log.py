import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel


class WorkoutLogCreate(BaseModel):
    workout_exercise_id: uuid.UUID


class WorkoutLogRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    workout_id: uuid.UUID | None = None
    exercise_id: uuid.UUID | None = None
    exercise_name: str
    muscle_group: str | None = None
    equipment: str | None = None
    day: int | None = None
    workout_date: date
    sets_data: list[dict[str, Any]]
    total_calories: Decimal | None = None
    completed_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
