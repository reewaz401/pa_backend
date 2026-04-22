import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from app.schemas.exercise import ExerciseRead


class SetCreate(BaseModel):
    set_index: int = 0
    reps: int | None = None
    weight: Decimal | None = None
    unit: str = "kg"
    is_warmup: bool = False
    rpe: Decimal | None = None
    rest_seconds: int | None = None
    calories_est: Decimal | None = None
    completed_at: datetime | None = None


class SetRead(BaseModel):
    id: uuid.UUID
    set_index: int
    reps: int | None = None
    weight: Decimal | None = None
    unit: str
    is_warmup: bool
    rpe: Decimal | None = None
    rest_seconds: int | None = None
    calories_est: Decimal | None = None
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class SetUpdate(BaseModel):
    set_index: int | None = None
    reps: int | None = None
    weight: Decimal | None = None
    unit: str | None = None
    is_warmup: bool | None = None
    rpe: Decimal | None = None
    rest_seconds: int | None = None
    calories_est: Decimal | None = None
    completed_at: datetime | None = None


class WorkoutExerciseCreate(BaseModel):
    exercise_id: uuid.UUID
    order_index: int = 0
    notes: str | None = None
    sets: list[SetCreate] = []


class WorkoutExerciseRead(BaseModel):
    id: uuid.UUID
    exercise_id: uuid.UUID
    exercise: ExerciseRead
    order_index: int
    calories_est: Decimal | None = None
    notes: str | None = None
    sets: list[SetRead] = []

    model_config = {"from_attributes": True}


class WorkoutCreate(BaseModel):
    workout_date: date
    day: int | None = None
    title: str | None = None
    notes: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_minutes: int | None = None
    intensity: int | None = None
    calories_est_total: Decimal | None = None
    exercises: list[WorkoutExerciseCreate] = []


class WorkoutRead(BaseModel):
    id: uuid.UUID
    workout_date: date
    day: int | None = None
    title: str | None = None
    notes: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_minutes: int | None = None
    intensity: int | None = None
    calories_est_total: Decimal | None = None
    created_at: datetime
    workout_exercises: list[WorkoutExerciseRead] = []

    model_config = {"from_attributes": True}


class WorkoutUpdate(BaseModel):
    workout_date: date | None = None
    day: int | None = None
    title: str | None = None
    notes: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_minutes: int | None = None
    intensity: int | None = None
    calories_est_total: Decimal | None = None
