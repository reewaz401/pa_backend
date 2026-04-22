import uuid
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.activity_log import ActivityLog
from app.models.user import User
from app.schemas.activity_log import ActivityLogRead, ActivityLogSummary

router = APIRouter(prefix="/activity-logs", tags=["activity-logs"])


@router.get("", response_model=list[ActivityLogRead])
async def list_activity_logs(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    event_type: str | None = Query(None),
    exercise_id: uuid.UUID | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(ActivityLog)
        .where(ActivityLog.user_id == current_user.id)
        .order_by(ActivityLog.event_date.desc(), ActivityLog.created_at.desc())
        .limit(limit)
    )
    if date_from:
        stmt = stmt.where(ActivityLog.event_date >= date_from)
    if date_to:
        stmt = stmt.where(ActivityLog.event_date <= date_to)
    if event_type:
        stmt = stmt.where(ActivityLog.event_type == event_type)
    if exercise_id:
        stmt = stmt.where(ActivityLog.exercise_id == exercise_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/summary", response_model=ActivityLogSummary)
async def activity_summary(
    date_from: date = Query(...),
    date_to: date = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    base = (
        select(ActivityLog)
        .where(
            ActivityLog.user_id == current_user.id,
            ActivityLog.event_date >= date_from,
            ActivityLog.event_date <= date_to,
        )
    )

    # Count workouts
    result = await db.execute(
        select(func.count())
        .select_from(ActivityLog)
        .where(
            ActivityLog.user_id == current_user.id,
            ActivityLog.event_date >= date_from,
            ActivityLog.event_date <= date_to,
            ActivityLog.event_type == "workout_completed",
        )
    )
    total_workouts = result.scalar() or 0

    # Count PRs
    result = await db.execute(
        select(func.count())
        .select_from(ActivityLog)
        .where(
            ActivityLog.user_id == current_user.id,
            ActivityLog.event_date >= date_from,
            ActivityLog.event_date <= date_to,
            ActivityLog.event_type == "personal_record",
        )
    )
    total_prs = result.scalar() or 0

    # Sum exercise-level stats from exercise_logged events
    result = await db.execute(
        select(ActivityLog.details)
        .where(
            ActivityLog.user_id == current_user.id,
            ActivityLog.event_date >= date_from,
            ActivityLog.event_date <= date_to,
            ActivityLog.event_type == "exercise_logged",
        )
    )
    total_exercises = 0
    total_calories = Decimal("0")
    total_volume = Decimal("0")
    for (details,) in result:
        total_exercises += 1
        if details.get("total_calories"):
            total_calories += Decimal(str(details["total_calories"]))
        if details.get("total_volume_kg"):
            total_volume += Decimal(str(details["total_volume_kg"]))

    return ActivityLogSummary(
        date_from=date_from,
        date_to=date_to,
        total_workouts=total_workouts,
        total_exercises_logged=total_exercises,
        total_calories=total_calories,
        total_volume_kg=total_volume,
        total_personal_records=total_prs,
    )
