from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.dependencies import get_current_user, get_db
from app.models.user import User, UserProfile
from app.schemas.user import UserProfileRead, UserProfileUpdate
from app.services.activity_logger import log_body_weight_updated

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/profile", response_model=UserProfileRead)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.id == current_user.id).options(selectinload(User.profile))
    )
    user = result.scalar_one()
    if user.profile is None:
        return UserProfileRead()
    return user.profile


@router.put("/me/profile", response_model=UserProfileRead)
async def upsert_profile(
    body: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.id == current_user.id).options(selectinload(User.profile))
    )
    user = result.scalar_one()
    data = body.model_dump(exclude_unset=True)

    # Capture old weight before update
    old_weight = None
    if user.profile and user.profile.weight_kg is not None:
        old_weight = float(user.profile.weight_kg)

    if user.profile is None:
        profile = UserProfile(user_id=user.id)
        for k, v in data.items():
            setattr(profile, k, v)
        db.add(profile)
    else:
        profile = user.profile
        for k, v in data.items():
            setattr(profile, k, v)

    # Emit body_weight_updated if weight changed
    new_weight = data.get("weight_kg")
    if new_weight is not None:
        new_weight_float = float(new_weight)
        if old_weight != new_weight_float:
            await log_body_weight_updated(
                db,
                user_id=current_user.id,
                old_weight=old_weight,
                new_weight=new_weight_float,
                event_date=date.today(),
            )

    await db.commit()
    await db.refresh(profile)
    return profile
