"""Specialty API endpoints."""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import get_current_user, require_role
from app.database import get_db
from app.modules.admin.models import Specialty
from app.modules.admin.schemas import SpecialtyCreate, SpecialtyResponse, SpecialtyUpdate
from app.modules.admin.service import (
    create_specialty,
    delete_specialty,
    get_all_specialties,
    get_specialty_by_id,
    update_specialty,
)
from app.modules.auth.models import User

router = APIRouter()


@router.get("/", response_model=list[SpecialtyResponse])
async def list_specialties(
    active_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_all_specialties(db, active_only=active_only)


@router.post("/", response_model=SpecialtyResponse, status_code=201)
async def create_new_specialty(
    body: SpecialtyCreate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    return await create_specialty(db, name=body.name, description=body.description)


@router.get("/{specialty_id}", response_model=SpecialtyResponse)
async def get_specialty(
    specialty_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    specialty = await get_specialty_by_id(db, specialty_id)
    if not specialty:
        raise HTTPException(status_code=404, detail="Especialidade não encontrada.")
    return specialty


@router.patch("/{specialty_id}", response_model=SpecialtyResponse)
async def update_existing_specialty(
    specialty_id: uuid.UUID,
    body: SpecialtyUpdate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    specialty = await get_specialty_by_id(db, specialty_id)
    if not specialty:
        raise HTTPException(status_code=404, detail="Especialidade não encontrada.")
    return await update_specialty(
        db, specialty, name=body.name, description=body.description, is_active=body.is_active
    )


@router.delete("/{specialty_id}", status_code=204)
async def delete_existing_specialty(
    specialty_id: uuid.UUID,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    specialty = await get_specialty_by_id(db, specialty_id)
    if not specialty:
        raise HTTPException(status_code=404, detail="Especialidade não encontrada.")
    await delete_specialty(db, specialty)
