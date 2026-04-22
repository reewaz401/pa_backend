import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserProfileRead(BaseModel):
    timezone: str | None = None
    weight_kg: Decimal | None = None
    height_cm: Decimal | None = None
    gender: str | None = None
    default_unit: str = "kg"

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    timezone: str | None = None
    weight_kg: Decimal | None = None
    height_cm: Decimal | None = None
    gender: str | None = None
    default_unit: str | None = None
