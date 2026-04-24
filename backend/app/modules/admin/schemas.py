"""Pydantic schemas for specialties."""
import uuid
from datetime import datetime

from pydantic import BaseModel


class SpecialtyCreate(BaseModel):
    name: str
    description: str | None = None


class SpecialtyUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class SpecialtyResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
