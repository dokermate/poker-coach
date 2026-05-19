from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.db.session import get_db
from app.db.models import Hand, GameSession, Table, User
from app.schemas import AnalyzeRequest, AdvisorOut, HandCreate, HandOut
from app.services.advisor_service import run_advisor
from app.services.bankroll_service import apply_hand_result
from app.services.alignment_service import compute_alignment

router = APIRouter(prefix="/hands", tags=["hands"])


@router.post("/analyze", response_model=AdvisorOut)
async def analyze(req: AnalyzeRequest):
    """Run advisor without saving — pure analysis endpoint."""
    result = run_advisor(req)
    return AdvisorOut(**result)


@router.post("", response_model=HandOut, status_code=201)
async def save_hand(
    req: HandCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Fetch session & table
    sess_r = await db.execute(
        select(GameSession).where(GameSession.id == req.session_id, GameSession.user_id == user.id)
    )
    session = sess_r.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")

    table_r = await db.execute(select(Table).where(Table.id == session.table_id))
    table = table_r.scalar_one()

    # Run advisor
    advice = run_advisor(req)

    # Financial result
    try:
        stack_before, stack_after, net_usd, net_bb = await apply_hand_result(
            db, session, None, table, req.net_usd, req.stack_after_usd
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    # Alignment
    aligned, ev_loss_bb, points = compute_alignment(
        req.user_action, advice["ev_comps"], advice["mix_json"]
    )

    # Update user points
    user.total_points += points

    # Build hand
    hand = Hand(
        session_id=req.session_id,
        user_id=user.id,
        hero_position=req.hero_position,
        villain_position=req.villain_position,
        hero_cards=",".join(req.hero_cards),
        board=",".join(req.board),
        street=req.street,
        pot_type=req.pot_type,
        hero_role=req.hero_role,
        preflop_spot=req.preflop_spot,
        pot_usd=req.pot_usd,
        recommended_action=advice["recommended_action"],
        recommended_size=advice["recommended_size"],
        equity=advice["equity"],
        ev_best_bb=advice["ev_best_bb"],
        ev_comps_json=advice["ev_comps"],
        mix_json=advice["mix_json"],
        explanation=advice["explanation"],
        user_action=req.user_action,
        stack_before_usd=stack_before,
        stack_after_usd=stack_after,
        net_usd=net_usd,
        net_bb=net_bb,
        aligned=aligned,
        ev_loss_bb=ev_loss_bb,
        points_earned=points,
    )
    db.add(hand)
    await db.commit()
    await db.refresh(hand)
    return hand


@router.get("", response_model=list[HandOut])
async def list_hands(
    session_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(Hand).where(Hand.user_id == user.id).order_by(Hand.played_at.desc())
    if session_id:
        q = q.where(Hand.session_id == session_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{hand_id}", response_model=HandOut)
async def get_hand(
    hand_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Hand).where(Hand.id == hand_id, Hand.user_id == user.id)
    )
    hand = result.scalar_one_or_none()
    if not hand:
        raise HTTPException(404, "Hand not found")
    return hand
