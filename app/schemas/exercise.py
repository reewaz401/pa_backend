import uuid
from datetime import datetime

from pydantic import BaseModel


class ExerciseCreate(BaseModel):
    name: str
    equipment: str | None = None
    muscle_group: str | None = None


class ExerciseRead(BaseModel):
    id: uuid.UUID
    name: str
    equipment: str | None = None
    muscle_group: str | None = None
    is_global: bool = False
    created_at: datetime
    calorie_weight_rate: float | None = None
    calorie_bodyweight_rate: float | None = None

    model_config = {"from_attributes": True}


class ExerciseUpdate(BaseModel):
    name: str | None = None
    equipment: str | None = None
    muscle_group: str | None = None
