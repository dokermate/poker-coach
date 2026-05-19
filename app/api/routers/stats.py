from __future__ import annotations
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.db.session import get_db
from app.db.models import User
from app.schemas import StatsSummary, EquityCurvePoint, LeakRow
from app.services import stats_service

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/summary", response_model=StatsSummary)
async def summary(
    session_id: Optional[int] = Query(None),
    table_id: Optional[int] = Query(None),
    from_dt: Optional[datetime] = Query(None, alias="from"),
    to_dt: Optional[datetime] = Query(None, alias="to"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await stats_service.get_summary(db, user.id, session_id, table_id, from_dt, to_dt)


@router.get("/equity-curve", response_model=list[EquityCurvePoint])
async def equity_curve(
    session_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await stats_service.get_equity_curve(db, user.id, session_id)


@router.get("/leaks", response_model=list[LeakRow])
async def leaks(
    session_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await stats_service.get_leaks(db, user.id, session_id)
