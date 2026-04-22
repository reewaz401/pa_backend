import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.calories import estimate_calories, get_user_weight
from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.workout import Workout, WorkoutExercise
from app.models.workout_log import WorkoutLog
from app.schemas.workout_log import WorkoutLogCreate, WorkoutLogRead
from app.services.activity_logger import log_exercise_logged, detect_and_log_pr

router = APIRouter(prefix="/workout-logs", tags=["workout-logs"])


@router.post("", response_model=WorkoutLogRead, status_code=status.HTTP_201_CREATED)
async def create_workout_log(
    body: WorkoutLogCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WorkoutExercise)
        .join(Workout)
        .where(
            WorkoutExercise.id == body.workout_exercise_id,
            Workout.user_id == current_user.id,
        )
        .options(
            selectinload(WorkoutExercise.exercise),
            selectinload(WorkoutExercise.sets),
            selectinload(WorkoutExercise.workout),
        )
    )
    we = result.scalar()
    if not we:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout exercise not found",
        )

    sets_data = [
        {
            "set_index": s.set_index,
            "reps": s.reps,
            "weight": float(s.weight) if s.weight is not None else None,
            "unit": s.unit,
            "is_warmup": s.is_warmup,
            "rpe": float(s.rpe) if s.rpe is not None else None,
        }
        for s in sorted(we.sets, key=lambda s: s.set_index)
    ]

    # Fetch user body weight for calorie estimation
    body_weight = await get_user_weight(current_user.id, db)
    total_calories = None
    if body_weight:
        total_calories = estimate_calories(
            sets_data,
            body_weight,
            we.exercise.muscle_group,
        )

    now = datetime.now(timezone.utc)
    today = now.date()

    log = WorkoutLog(
        user_id=current_user.id,
        workout_id=we.workout_id,
        exercise_id=we.exercise_id,
        exercise_name=we.exercise.name,
        muscle_group=we.exercise.muscle_group,
        equipment=we.exercise.equipment,
        day=we.workout.day,
        workout_date=today,
        sets_data=sets_data,
        total_calories=total_calories,
        completed_at=now,
    )
    db.add(log)

    # Emit activity logs
    await log_exercise_logged(
        db,
        user_id=current_user.id,
        exercise_name=we.exercise.name,
        muscle_group=we.exercise.muscle_group,
        sets_data=sets_data,
        total_calories=total_calories,
        workout_id=we.workout_id,
        exercise_id=we.exercise_id,
        workout_date=today,
    )
    await detect_and_log_pr(
        db,
        user_id=current_user.id,
        exercise_id=we.exercise_id,
        exercise_name=we.exercise.name,
        muscle_group=we.exercise.muscle_group,
        sets_data=sets_data,
        workout_id=we.workout_id,
        workout_date=today,
    )

    await db.commit()
    await db.refresh(log)
    return log


@router.get("", response_model=list[WorkoutLogRead])
async def list_workout_logs(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    exercise_id: uuid.UUID | None = Query(None),
    limit: int | None = Query(None, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(WorkoutLog)
        .where(WorkoutLog.user_id == current_user.id)
        .order_by(WorkoutLog.completed_at.desc())
    )
    if date_from:
        stmt = stmt.where(WorkoutLog.workout_date >= date_from)
    if date_to:
        stmt = stmt.where(WorkoutLog.workout_date <= date_to)
    if exercise_id:
        stmt = stmt.where(WorkoutLog.exercise_id == exercise_id)
    if limit:
        stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/latest", response_model=list[WorkoutLogRead])
async def latest_workout_logs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get workout logs from the most recent completed workout date."""
    # Find the latest workout_date
    latest_date = await db.scalar(
        select(WorkoutLog.workout_date)
        .where(WorkoutLog.user_id == current_user.id)
        .order_by(WorkoutLog.workout_date.desc())
        .limit(1)
    )
    if not latest_date:
        return []

    result = await db.execute(
        select(WorkoutLog)
        .where(
            WorkoutLog.user_id == current_user.id,
            WorkoutLog.workout_date == latest_date,
        )
        .order_by(WorkoutLog.completed_at.desc())
    )
    return result.scalars().all()


@router.get("/{log_id}", response_model=WorkoutLogRead)
async def get_workout_log(
    log_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    log = await db.scalar(
        select(WorkoutLog).where(
            WorkoutLog.id == log_id,
            WorkoutLog.user_id == current_user.id,
        )
    )
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout log not found",
        )
    return log


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workout_log(
    log_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    log = await db.scalar(
        select(WorkoutLog).where(
            WorkoutLog.id == log_id,
            WorkoutLog.user_id == current_user.id,
        )
    )
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout log not found",
        )
    await db.delete(log)
    await db.commit()
