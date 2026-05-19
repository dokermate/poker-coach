from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.db.session import get_db
from app.db.models import GameSession, User
from app.schemas import SessionCreate, SessionOut, RebuyCreate
from app.services.bankroll_service import open_session, close_session
from app.db.models import Rebuy

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionOut, status_code=201)
async def create_session(
    req: SessionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        session = await open_session(db, user.id, req.table_id, req.start_stack_usd)
        await db.commit()
        await db.refresh(session)
        return session
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("", response_model=list[SessionOut])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(GameSession).where(GameSession.user_id == user.id).order_by(GameSession.started_at.desc())
    )
    return result.scalars().all()


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(GameSession).where(GameSession.id == session_id, GameSession.user_id == user.id)
    )
    sess = result.scalar_one_or_none()
    if not sess:
        raise HTTPException(404, "Session not found")
    return sess


@router.post("/{session_id}/close", response_model=SessionOut)
async def end_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(GameSession).where(GameSession.id == session_id, GameSession.user_id == user.id)
    )
    sess = result.scalar_one_or_none()
    if not sess:
        raise HTTPException(404, "Session not found")
    await close_session(db, sess)
    await db.commit()
    await db.refresh(sess)
    return sess


@router.post("/{session_id}/rebuy", status_code=201)
async def add_rebuy(
    session_id: int,
    req: RebuyCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(GameSession).where(GameSession.id == session_id, GameSession.user_id == user.id)
    )
    sess = result.scalar_one_or_none()
    if not sess:
        raise HTTPException(404, "Session not found")
    rebuy = Rebuy(session_id=session_id, rebuy_usd=req.rebuy_usd)
    sess.current_stack_usd += req.rebuy_usd
    db.add(rebuy)
    await db.commit()
    return {"session_id": session_id, "rebuy_usd": req.rebuy_usd, "current_stack_usd": sess.current_stack_usd}
