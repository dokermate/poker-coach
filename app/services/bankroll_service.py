"""Financial calculations for sessions and hands."""
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import GameSession, Hand, Table, User


async def open_session(
    db: AsyncSession,
    user_id: int,
    table_id: int,
    start_stack_usd: float,
) -> GameSession:
    result = await db.execute(select(Table).where(Table.id == table_id, Table.owner_id == user_id))
    table = result.scalar_one_or_none()
    if table is None:
        raise ValueError(f"Table {table_id} not found for user {user_id}")

    session = GameSession(
        user_id=user_id,
        table_id=table_id,
        start_stack_usd=start_stack_usd,
        start_stack_bb=round(start_stack_usd / table.bb_usd, 2),
        current_stack_usd=start_stack_usd,
        status="active",
    )
    db.add(session)
    await db.flush()
    return session


async def close_session(db: AsyncSession, session: GameSession) -> None:
    from datetime import datetime, timezone
    session.status = "completed"
    session.ended_at = datetime.now(timezone.utc)


async def apply_hand_result(
    db: AsyncSession,
    session: GameSession,
    hand: Hand,
    table: Table,
    net_usd: float | None,
    stack_after_usd: float | None,
) -> tuple[float, float, float]:
    """
    Resolve financial fields and update session stack.
    Returns (stack_before, stack_after, net_usd).
    """
    stack_before = session.current_stack_usd

    if net_usd is not None:
        resolved_after = stack_before + net_usd
        resolved_net = net_usd
    elif stack_after_usd is not None:
        resolved_after = stack_after_usd
        resolved_net = stack_after_usd - stack_before
    else:
        raise ValueError("Provide either net_usd or stack_after_usd")

    net_bb = resolved_net / table.bb_usd
    session.current_stack_usd = resolved_after

    # Update user lifetime P&L
    result = await db.execute(select(User).where(User.id == session.user_id))
    user = result.scalar_one()
    user.lifetime_pnl_usd = round(user.lifetime_pnl_usd + resolved_net, 4)

    return stack_before, resolved_after, resolved_net, round(net_bb, 4)
