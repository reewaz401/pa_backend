import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.calories import estimate_calories, get_user_weight
from app.dependencies import get_current_user, get_db
from app.models.exercise import Exercise
from app.models.set import Set
from app.models.user import User
from app.models.workout import Workout, WorkoutExercise
from app.models.workout_log import WorkoutLog
from app.schemas.workout import (
    SetCreate,
    SetRead,
    SetUpdate,
    WorkoutCreate,
    WorkoutExerciseCreate,
    WorkoutExerciseRead,
    WorkoutRead,
    WorkoutUpdate,
)
from app.services.activity_logger import (
    log_exercise_logged,
    detect_and_log_pr,
    log_workout_completed,
)

router = APIRouter(prefix="/workouts", tags=["workouts"])


async def _recalc_we_calories(
    we: WorkoutExercise, user_id, db: AsyncSession
) -> None:
    """Recalculate calories_est on a WorkoutExercise from its sets."""
    body_weight = await get_user_weight(user_id, db)
    if not body_weight:
        we.calories_est = None
        return
    # Load exercise if not already loaded
    exercise = await db.get(Exercise, we.exercise_id)
    # Load sets
    await db.refresh(we, ["sets"])
    sets_data = [
        {
            "reps": s.reps,
            "weight": float(s.weight) if s.weight is not None else 0.0,
            "is_warmup": s.is_warmup,
        }
        for s in we.sets
    ]
    we.calories_est = estimate_calories(sets_data, body_weight, exercise.muscle_group if exercise else None)

_eager = (
    selectinload(Workout.workout_exercises)
    .selectinload(WorkoutExercise.exercise),
    selectinload(Workout.workout_exercises)
    .selectinload(WorkoutExercise.sets),
)


async def _get_owned_workout(
    workout_id: uuid.UUID, user: User, db: AsyncSession
) -> Workout:
    result = await db.execute(
        select(Workout)
        .where(Workout.id == workout_id, Workout.user_id == user.id)
        .options(*_eager)
    )
    workout = result.scalar()
    if not workout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")
    return workout


# ── Workout CRUD ────────────────────────────────────────────────

@router.post("", response_model=WorkoutRead, status_code=status.HTTP_201_CREATED)
async def create_workout(
    body: WorkoutCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = body.model_dump(exclude={"exercises"})
    workout = Workout(user_id=current_user.id, **data)
    for we_data in body.exercises:
        we = WorkoutExercise(
            exercise_id=we_data.exercise_id,
            order_index=we_data.order_index,
            notes=we_data.notes,
        )
        for s_data in we_data.sets:
            we.sets.append(Set(**s_data.model_dump()))
        workout.workout_exercises.append(we)
    db.add(workout)
    await db.flush()
    for we in workout.workout_exercises:
        await _recalc_we_calories(we, current_user.id, db)
    await _recalc_workout_total(workout, db)
    await db.commit()
    return await _get_owned_workout(workout.id, current_user, db)


@router.get("", response_model=list[WorkoutRead])
async def list_workouts(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Workout)
        .where(Workout.user_id == current_user.id)
        .options(*_eager)
        .order_by(Workout.workout_date.desc())
    )
    if date_from:
        stmt = stmt.where(Workout.workout_date >= date_from)
    if date_to:
        stmt = stmt.where(Workout.workout_date <= date_to)
    result = await db.execute(stmt)
    return result.scalars().unique().all()


@router.get("/{workout_id}", response_model=WorkoutRead)
async def get_workout(
    workout_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_owned_workout(workout_id, current_user, db)


@router.patch("/{workout_id}", response_model=WorkoutRead)
async def update_workout(
    workout_id: uuid.UUID,
    body: WorkoutUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workout = await _get_owned_workout(workout_id, current_user, db)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(workout, k, v)
    await db.commit()
    return await _get_owned_workout(workout_id, current_user, db)


@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workout(
    workout_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workout = await _get_owned_workout(workout_id, current_user, db)
    await db.delete(workout)
    await db.commit()


async def _recalc_workout_total(workout: Workout, db: AsyncSession) -> None:
    """Sum calories_est from all workout_exercises into workout.calories_est_total."""
    await db.refresh(workout, ["workout_exercises"])
    total = Decimal("0")
    for we in workout.workout_exercises:
        if we.calories_est:
            total += we.calories_est
    workout.calories_est_total = total if total > 0 else None


@router.post("/{workout_id}/complete", response_model=WorkoutRead)
async def complete_workout(
    workout_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workout = await _get_owned_workout(workout_id, current_user, db)

    now = datetime.now(timezone.utc)

    # Set ended_at if not already set
    if not workout.ended_at:
        workout.ended_at = now

    # Update workout_date to the actual completion date
    workout.workout_date = now.date()

    # Recalc calories for all exercises and auto-create missing workout_logs
    body_weight = await get_user_weight(current_user.id, db)
    total_sets = 0
    total_volume = 0.0

    for we in workout.workout_exercises:
        await _recalc_we_calories(we, current_user.id, db)
        await db.refresh(we, ["sets"])
        exercise = await db.get(Exercise, we.exercise_id)

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

        working_sets = [s for s in sets_data if not s.get("is_warmup", False)]
        total_sets += len(working_sets)
        total_volume += sum(
            (s.get("reps") or 0) * (s.get("weight") or 0) for s in working_sets
        )

        # Check if workout_log already exists for this workout_exercise
        existing_log = await db.scalar(
            select(WorkoutLog).where(
                WorkoutLog.user_id == current_user.id,
                WorkoutLog.workout_id == workout.id,
                WorkoutLog.exercise_id == we.exercise_id,
            )
        )
        if not existing_log:
            total_calories = None
            if body_weight:
                total_calories = estimate_calories(
                    sets_data, body_weight, exercise.muscle_group if exercise else None
                )
            wl = WorkoutLog(
                user_id=current_user.id,
                workout_id=workout.id,
                exercise_id=we.exercise_id,
                exercise_name=exercise.name if exercise else "Unknown",
                muscle_group=exercise.muscle_group if exercise else None,
                equipment=exercise.equipment if exercise else None,
                day=workout.day,
                workout_date=workout.workout_date,
                sets_data=sets_data,
                total_calories=total_calories,
                completed_at=datetime.now(timezone.utc),
            )
            db.add(wl)

            # Emit activity logs for each auto-created workout_log
            await log_exercise_logged(
                db,
                user_id=current_user.id,
                exercise_name=exercise.name if exercise else "Unknown",
                muscle_group=exercise.muscle_group if exercise else None,
                sets_data=sets_data,
                total_calories=total_calories,
                workout_id=workout.id,
                exercise_id=we.exercise_id,
                workout_date=workout.workout_date,
            )
            await detect_and_log_pr(
                db,
                user_id=current_user.id,
                exercise_id=we.exercise_id,
                exercise_name=exercise.name if exercise else "Unknown",
                muscle_group=exercise.muscle_group if exercise else None,
                sets_data=sets_data,
                workout_id=workout.id,
                workout_date=workout.workout_date,
            )

    # Auto-sum calories
    await _recalc_workout_total(workout, db)

    # Emit workout_completed activity log
    await log_workout_completed(
        db,
        user_id=current_user.id,
        workout_id=workout.id,
        workout_date=workout.workout_date,
        title=workout.title,
        duration_minutes=workout.duration_minutes,
        total_calories=workout.calories_est_total,
        exercise_count=len(workout.workout_exercises),
        total_sets=total_sets,
        total_volume_kg=total_volume,
    )

    await db.commit()
    return await _get_owned_workout(workout.id, current_user, db)


# ── Workout Exercises ───────────────────────────────────────────

@router.post(
    "/{workout_id}/exercises",
    response_model=WorkoutExerciseRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_workout_exercise(
    workout_id: uuid.UUID,
    body: WorkoutExerciseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_workout(workout_id, current_user, db)
    we = WorkoutExercise(
        workout_id=workout_id,
        exercise_id=body.exercise_id,
        order_index=body.order_index,
        notes=body.notes,
    )
    for s_data in body.sets:
        we.sets.append(Set(**s_data.model_dump()))
    db.add(we)
    await db.flush()
    await _recalc_we_calories(we, current_user.id, db)
    parent_workout = await _get_owned_workout(workout_id, current_user, db)
    await _recalc_workout_total(parent_workout, db)
    await db.commit()
    result = await db.execute(
        select(WorkoutExercise)
        .where(WorkoutExercise.id == we.id)
        .options(
            selectinload(WorkoutExercise.exercise),
            selectinload(WorkoutExercise.sets),
        )
    )
    return result.scalar_one()


@router.delete(
    "/{workout_id}/exercises/{we_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_workout_exercise(
    workout_id: uuid.UUID,
    we_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_workout(workout_id, current_user, db)
    we = await db.scalar(
        select(WorkoutExercise).where(
            WorkoutExercise.id == we_id,
            WorkoutExercise.workout_id == workout_id,
        )
    )
    if not we:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout exercise not found")
    await db.delete(we)
    await db.commit()


# ── Sets ────────────────────────────────────────────────────────

@router.post(
    "/{workout_id}/exercises/{we_id}/sets",
    response_model=SetRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_set(
    workout_id: uuid.UUID,
    we_id: uuid.UUID,
    body: SetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_workout(workout_id, current_user, db)
    we = await db.scalar(
        select(WorkoutExercise).where(
            WorkoutExercise.id == we_id,
            WorkoutExercise.workout_id == workout_id,
        )
    )
    if not we:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout exercise not found")
    s = Set(workout_exercise_id=we_id, **body.model_dump())
    db.add(s)
    await db.flush()
    await _recalc_we_calories(we, current_user.id, db)
    parent_workout = await _get_owned_workout(workout_id, current_user, db)
    await _recalc_workout_total(parent_workout, db)
    await db.commit()
    await db.refresh(s)
    return s


# Sets PATCH/DELETE are at top-level /sets path for convenience
sets_router = APIRouter(tags=["sets"])


@sets_router.patch("/sets/{set_id}", response_model=SetRead)
async def update_set(
    set_id: uuid.UUID,
    body: SetUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Set)
        .join(WorkoutExercise)
        .join(Workout)
        .where(Set.id == set_id, Workout.user_id == current_user.id)
    )
    s = result.scalar()
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Set not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    we = await db.get(WorkoutExercise, s.workout_exercise_id)
    await _recalc_we_calories(we, current_user.id, db)
    workout = await db.get(Workout, we.workout_id)
    if workout:
        await _recalc_workout_total(workout, db)
    await db.commit()
    await db.refresh(s)
    return s


@sets_router.delete("/sets/{set_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_set(
    set_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Set)
        .join(WorkoutExercise)
        .join(Workout)
        .where(Set.id == set_id, Workout.user_id == current_user.id)
    )
    s = result.scalar()
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Set not found")
    we_id = s.workout_exercise_id
    await db.delete(s)
    await db.flush()
    we = await db.get(WorkoutExercise, we_id)
    if we:
        await _recalc_we_calories(we, current_user.id, db)
        workout = await db.get(Workout, we.workout_id)
        if workout:
            await _recalc_workout_total(workout, db)
    await db.commit()
