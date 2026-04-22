"""Service for creating activity log entries.

All functions add to the session but do NOT commit — the caller handles the transaction.
"""
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_log import ActivityLog
from app.models.workout_log import WorkoutLog


async def log_exercise_logged(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    exercise_name: str,
    muscle_group: str | None,
    sets_data: list[dict],
    total_calories: Decimal | None,
    workout_id: uuid.UUID | None,
    exercise_id: uuid.UUID | None,
    workout_date: date,
) -> ActivityLog:
    """Create an exercise_logged activity log entry."""
    working_sets = [s for s in sets_data if not s.get("is_warmup", False)]
    total_reps = sum(s.get("reps") or 0 for s in working_sets)
    max_weight = max((s.get("weight") or 0 for s in working_sets), default=0)
    total_volume = sum(
        (s.get("reps") or 0) * (s.get("weight") or 0) for s in working_sets
    )

    # Build set descriptions like "10×60kg, 8×70kg"
    set_parts = []
    for s in working_sets:
        reps = s.get("reps") or 0
        weight = s.get("weight")
        unit = s.get("unit", "kg")
        if weight:
            set_parts.append(f"{reps}×{weight}{unit}")
        else:
            set_parts.append(f"{reps} reps")

    sets_desc = ", ".join(set_parts)
    muscle_label = f" ({muscle_group})" if muscle_group else ""
    cal_label = f" | ~{total_calories} cal" if total_calories else ""
    summary = (
        f"Logged {exercise_name}{muscle_label}: "
        f"{len(working_sets)} sets — {sets_desc}{cal_label}"
    )

    entry = ActivityLog(
        user_id=user_id,
        event_type="exercise_logged",
        event_date=workout_date,
        summary=summary,
        details={
            "exercise_name": exercise_name,
            "muscle_group": muscle_group,
            "sets_count": len(working_sets),
            "total_reps": total_reps,
            "max_weight": float(max_weight),
            "total_volume_kg": float(total_volume),
            "total_calories": float(total_calories) if total_calories else None,
            "sets": [
                {
                    "reps": s.get("reps"),
                    "weight": s.get("weight"),
                    "unit": s.get("unit", "kg"),
                }
                for s in working_sets
            ],
        },
        workout_id=workout_id,
        exercise_id=exercise_id,
    )
    db.add(entry)
    return entry


async def detect_and_log_pr(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    exercise_id: uuid.UUID | None,
    exercise_name: str,
    muscle_group: str | None,
    sets_data: list[dict],
    workout_id: uuid.UUID | None,
    workout_date: date,
) -> ActivityLog | None:
    """Check if max weight in this session is a personal record. Return log entry or None."""
    if not exercise_id:
        return None

    working_sets = [s for s in sets_data if not s.get("is_warmup", False)]
    current_max = max((s.get("weight") or 0 for s in working_sets), default=0)
    if current_max <= 0:
        return None

    # Find previous max weight for this exercise across all workout_logs
    result = await db.execute(
        select(WorkoutLog.sets_data).where(
            WorkoutLog.user_id == user_id,
            WorkoutLog.exercise_id == exercise_id,
        )
    )
    previous_max = 0.0
    for (row_sets_data,) in result:
        for s in row_sets_data:
            if s.get("is_warmup", False):
                continue
            w = s.get("weight") or 0
            if w > previous_max:
                previous_max = w

    if current_max <= previous_max:
        return None

    # It's a PR!
    summary = (
        f"New personal record on {exercise_name}: "
        f"{current_max}kg (previous best: {previous_max}kg)"
    )
    entry = ActivityLog(
        user_id=user_id,
        event_type="personal_record",
        event_date=workout_date,
        summary=summary,
        details={
            "exercise_name": exercise_name,
            "muscle_group": muscle_group,
            "new_max_weight": float(current_max),
            "previous_max_weight": float(previous_max),
        },
        workout_id=workout_id,
        exercise_id=exercise_id,
    )
    db.add(entry)
    return entry


async def log_workout_completed(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    workout_id: uuid.UUID,
    workout_date: date,
    title: str | None,
    duration_minutes: int | None,
    total_calories: Decimal | None,
    exercise_count: int,
    total_sets: int,
    total_volume_kg: float,
) -> ActivityLog:
    """Create a workout_completed activity log entry."""
    parts = []
    if title:
        parts.append(title)
    else:
        parts.append("Workout")
    parts.append(f"completed: {exercise_count} exercises, {total_sets} sets")
    if total_volume_kg:
        parts.append(f"{total_volume_kg:.0f}kg total volume")
    if total_calories:
        parts.append(f"~{total_calories} cal")
    if duration_minutes:
        parts.append(f"{duration_minutes} min")
    summary = " | ".join(parts)

    entry = ActivityLog(
        user_id=user_id,
        event_type="workout_completed",
        event_date=workout_date,
        summary=summary,
        details={
            "title": title,
            "exercise_count": exercise_count,
            "total_sets": total_sets,
            "total_volume_kg": total_volume_kg,
            "total_calories": float(total_calories) if total_calories else None,
            "duration_minutes": duration_minutes,
        },
        workout_id=workout_id,
    )
    db.add(entry)
    return entry


async def log_body_weight_updated(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    old_weight: float | None,
    new_weight: float,
    event_date: date,
) -> ActivityLog:
    """Create a body_weight_updated activity log entry."""
    if old_weight:
        diff = new_weight - old_weight
        direction = "up" if diff > 0 else "down"
        summary = (
            f"Body weight updated: {old_weight}kg → {new_weight}kg "
            f"({direction} {abs(diff):.1f}kg)"
        )
    else:
        summary = f"Body weight set to {new_weight}kg"

    entry = ActivityLog(
        user_id=user_id,
        event_type="body_weight_updated",
        event_date=event_date,
        summary=summary,
        details={
            "old_weight_kg": old_weight,
            "new_weight_kg": new_weight,
        },
    )
    db.add(entry)
    return entry
