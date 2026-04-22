import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel


class ActivityLogRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    event_type: str
    event_date: date
    summary: str
    details: dict[str, Any]
    workout_id: uuid.UUID | None = None
    exercise_id: uuid.UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ActivityLogSummary(BaseModel):
    date_from: date
    date_to: date
    total_workouts: int = 0
    total_exercises_logged: int = 0
    total_calories: Decimal = Decimal("0")
    total_volume_kg: Decimal = Decimal("0")
    total_personal_records: int = 0
