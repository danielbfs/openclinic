"""Follow-up rules and jobs API endpoints."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.permissions import require_role
from app.modules.followup import service
from app.modules.followup.schemas import (
    FollowupJobResponse,
    FollowupRuleCreate,
    FollowupRuleResponse,
    FollowupRuleUpdate,
)

router = APIRouter()


# --- Rules ---


@router.get("/rules", response_model=list[FollowupRuleResponse])
async def list_rules(
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("admin")),
):
    return await service.get_all_rules(db)


@router.post("/rules", response_model=FollowupRuleResponse, status_code=201)
async def create_rule(
    payload: FollowupRuleCreate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("admin")),
):
    return await service.create_rule(db, **payload.model_dump())


@router.get("/rules/{rule_id}", response_model=FollowupRuleResponse)
async def get_rule(
    rule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("admin")),
):
    rule = await service.get_rule_by_id(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.patch("/rules/{rule_id}", response_model=FollowupRuleResponse)
async def update_rule(
    rule_id: uuid.UUID,
    payload: FollowupRuleUpdate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("admin")),
):
    rule = await service.get_rule_by_id(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return await service.update_rule(db, rule, **payload.model_dump(exclude_unset=True))


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_rule(
    rule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("admin")),
):
    rule = await service.get_rule_by_id(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    await service.delete_rule(db, rule)


# --- Jobs ---


@router.get("/jobs", response_model=list[FollowupJobResponse])
async def list_jobs(
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role("admin")),
):
    return await service.get_jobs(db, status=status, limit=limit)
