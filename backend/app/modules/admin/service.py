"""Specialty business logic."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin.models import Specialty


async def get_all_specialties(db: AsyncSession, active_only: bool = False) -> list[Specialty]:
    query = select(Specialty).order_by(Specialty.name)
    if active_only:
        query = query.where(Specialty.is_active == True)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_specialty_by_id(db: AsyncSession, specialty_id: uuid.UUID) -> Specialty | None:
    result = await db.execute(select(Specialty).where(Specialty.id == specialty_id))
    return result.scalar_one_or_none()


async def create_specialty(db: AsyncSession, name: str, description: str | None = None) -> Specialty:
    specialty = Specialty(name=name, description=description)
    db.add(specialty)
    await db.commit()
    await db.refresh(specialty)
    return specialty


async def update_specialty(
    db: AsyncSession,
    specialty: Specialty,
    name: str | None = None,
    description: str | None = None,
    is_active: bool | None = None,
) -> Specialty:
    if name is not None:
        specialty.name = name
    if description is not None:
        specialty.description = description
    if is_active is not None:
        specialty.is_active = is_active
    await db.commit()
    await db.refresh(specialty)
    return specialty


async def delete_specialty(db: AsyncSession, specialty: Specialty) -> None:
    specialty.is_active = False
    await db.commit()
