from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserProfile

# MET multipliers by muscle group — compound movements burn more
MET_FACTORS: dict[str | None, float] = {
    "Legs": 6.0,
    "Back": 5.0,
    "Chest": 5.0,
    "Shoulders": 4.0,
    "Arms": 3.5,
    "Biceps": 3.5,
    "Triceps": 3.5,
    "Core": 3.5,
    "Abs": 3.5,
    "Glutes": 5.5,
    "Cardio": 7.0,
    None: 4.0,
}


def estimate_calories(
    sets_data: list[dict],
    body_weight_kg: float,
    muscle_group: str | None,
) -> Decimal:
    """Per set: (reps x weight x 0.0004 + reps x body_weight x 0.00015) x MET_factor"""
    met = MET_FACTORS.get(muscle_group, MET_FACTORS[None])
    total = 0.0
    for s in sets_data:
        if s.get("is_warmup", False):
            continue
        reps = s.get("reps") or 0
        weight = s.get("weight") or 0.0
        set_cal = (reps * weight * 0.0004 + reps * body_weight_kg * 0.00015) * met
        total += set_cal
    return Decimal(str(round(total, 2)))


def calorie_rates(body_weight_kg: float, muscle_group: str | None) -> tuple[float, float]:
    """Return (weight_rate, bodyweight_rate) for client-side calculation."""
    met = MET_FACTORS.get(muscle_group, MET_FACTORS[None])
    return (
        round(0.0004 * met, 6),
        round(body_weight_kg * 0.00015 * met, 6),
    )


async def get_user_weight(user_id, db: AsyncSession) -> float | None:
    profile = await db.scalar(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    if profile and profile.weight_kg:
        return float(profile.weight_kg)
    return None
