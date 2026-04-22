import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.calories import calorie_rates, get_user_weight
from app.dependencies import get_current_user, get_db
from app.models.exercise import Exercise
from app.models.user import User
from app.schemas.exercise import ExerciseCreate, ExerciseRead, ExerciseUpdate

router = APIRouter(prefix="/exercises", tags=["exercises"])


def _with_calorie_rates(exercise: Exercise, body_weight_kg: float | None) -> dict:
    data = ExerciseRead.model_validate(exercise).model_dump()
    if body_weight_kg:
        wr, bwr = calorie_rates(body_weight_kg, exercise.muscle_group)
        data["calorie_weight_rate"] = wr
        data["calorie_bodyweight_rate"] = bwr
    return data


async def _get_visible_exercise(
    exercise_id: uuid.UUID, user: User, db: AsyncSession
) -> Exercise:
    exercise = await db.scalar(
        select(Exercise).where(
            Exercise.id == exercise_id,
            or_(Exercise.user_id == user.id, Exercise.is_global.is_(True)),
        )
    )
    if not exercise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")
    return exercise


@router.post("", response_model=ExerciseRead, status_code=status.HTTP_201_CREATED)
async def create_exercise(
    body: ExerciseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    exercise = Exercise(user_id=current_user.id, **body.model_dump())
    db.add(exercise)
    await db.commit()
    await db.refresh(exercise)
    weight = await get_user_weight(current_user.id, db)
    return _with_calorie_rates(exercise, weight)


@router.get("", response_model=list[ExerciseRead])
async def list_exercises(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.scalars(
        select(Exercise)
        .where(or_(Exercise.user_id == current_user.id, Exercise.is_global.is_(True)))
        .order_by(Exercise.name)
    )
    weight = await get_user_weight(current_user.id, db)
    return [_with_calorie_rates(e, weight) for e in result.all()]


@router.get("/{exercise_id}", response_model=ExerciseRead)
async def get_exercise(
    exercise_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    exercise = await _get_visible_exercise(exercise_id, current_user, db)
    weight = await get_user_weight(current_user.id, db)
    return _with_calorie_rates(exercise, weight)


@router.patch("/{exercise_id}", response_model=ExerciseRead)
async def update_exercise(
    exercise_id: uuid.UUID,
    body: ExerciseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    exercise = await _get_visible_exercise(exercise_id, current_user, db)
    if exercise.is_global:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify a global exercise",
        )
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(exercise, k, v)
    await db.commit()
    await db.refresh(exercise)
    weight = await get_user_weight(current_user.id, db)
    return _with_calorie_rates(exercise, weight)


@router.delete("/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exercise(
    exercise_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    exercise = await _get_visible_exercise(exercise_id, current_user, db)
    if exercise.is_global:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete a global exercise",
        )
    await db.delete(exercise)
    await db.commit()
