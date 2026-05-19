"""Stats computation — P&L, alignment, leaks, equity curve."""
from __future__ import annotations
from datetime import datetime
from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Hand, GameSession, User
from app.schemas import StatsSummary, EquityCurvePoint, LeakRow
from app.services.alignment_service import session_bonus


async def _get_hands(
    db: AsyncSession,
    user_id: int,
    session_id: int | None = None,
    table_id: int | None = None,
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
) -> list[Hand]:
    q = select(Hand).where(Hand.user_id == user_id)
    if session_id:
        q = q.where(Hand.session_id == session_id)
    if table_id:
        q = q.join(GameSession, GameSession.id == Hand.session_id).where(
            GameSession.table_id == table_id
        )
    if from_dt:
        q = q.where(Hand.played_at >= from_dt)
    if to_dt:
        q = q.where(Hand.played_at <= to_dt)
    q = q.order_by(Hand.played_at)
    result = await db.execute(q)
    return list(result.scalars().all())


def _drawdown(net_usds: list[float]) -> tuple[float, float, float]:
    """Max drawdown over a sequence of net P&L values."""
    cumulative = 0.0
    peak = 0.0
    max_dd = 0.0
    for v in net_usds:
        cumulative += v
        if cumulative > peak:
            peak = cumulative
        dd = peak - cumulative
        if dd > max_dd:
            max_dd = dd
    return round(max_dd, 4)


async def get_summary(
    db: AsyncSession,
    user_id: int,
    session_id: int | None,
    table_id: int | None,
    from_dt: datetime | None,
    to_dt: datetime | None,
) -> StatsSummary:
    hands = await _get_hands(db, user_id, session_id, table_id, from_dt, to_dt)

    n = len(hands)
    session_pnl_usd = sum(h.net_usd for h in hands)
    ev_loss_total = sum(h.ev_loss_bb for h in hands)
    aligned_count = sum(1 for h in hands if h.aligned)
    alignment_rate = aligned_count / n if n else 0.0
    net_bbs = [h.net_bb for h in hands]
    session_pnl_bb = sum(net_bbs)
    bb_per_100 = (session_pnl_bb / n * 100) if n else 0.0

    # ROI: pnl / total invested (use start stack of session if available)
    if session_id:
        r = await db.execute(select(GameSession).where(GameSession.id == session_id))
        sess = r.scalar_one_or_none()
        invested = sess.start_stack_usd if sess else 1
    else:
        invested = 1
    roi_pct = (session_pnl_usd / invested * 100) if invested else 0.0

    # Drawdown
    max_dd_usd = _drawdown([h.net_usd for h in hands])
    # For bb drawdown we need bb_usd — approximate from net_bb
    if hands and any(h.net_usd != 0 for h in hands):
        sample = next(h for h in hands if h.net_usd != 0)
        bb_usd = abs(sample.net_usd / sample.net_bb) if sample.net_bb != 0 else 1
    else:
        bb_usd = 1.0
    max_dd_bb = max_dd_usd / bb_usd if bb_usd else 0.0

    # User lifetime
    r = await db.execute(select(User).where(User.id == user_id))
    user = r.scalar_one()

    # Session bonus points
    bonus = session_bonus(alignment_rate, n)
    total_pts = user.total_points + bonus  # bonus not persisted here; just shown

    return StatsSummary(
        hands_played=n,
        session_pnl_usd=round(session_pnl_usd, 4),
        session_pnl_bb=round(session_pnl_bb, 4),
        roi_session_pct=round(roi_pct, 2),
        bb_per_100=round(bb_per_100, 2),
        lifetime_pnl_usd=round(user.lifetime_pnl_usd, 4),
        alignment_rate_pct=round(alignment_rate * 100, 2),
        ev_loss_bb_total=round(ev_loss_total, 4),
        total_points=total_pts,
        max_drawdown_usd=round(max_dd_usd, 4),
        max_drawdown_bb=round(max_dd_bb, 4),
    )


async def get_equity_curve(
    db: AsyncSession,
    user_id: int,
    session_id: int | None,
) -> list[EquityCurvePoint]:
    hands = await _get_hands(db, user_id, session_id)
    cumulative = 0.0
    points = []
    for h in hands:
        cumulative += h.net_usd
        points.append(EquityCurvePoint(
            played_at=h.played_at,
            cumulative_pnl_usd=round(cumulative, 4),
            current_stack_usd=h.stack_after_usd,
        ))
    return points


async def get_leaks(
    db: AsyncSession,
    user_id: int,
    session_id: int | None,
) -> list[LeakRow]:
    hands = await _get_hands(db, user_id, session_id)

    groups: dict[str, list[Hand]] = defaultdict(list)
    for h in hands:
        key = f"{h.hero_position}|{h.street}|{h.pot_type}"
        groups[key].append(h)

    rows = []
    for key, hs in groups.items():
        n = len(hs)
        net_bb = sum(x.net_bb for x in hs)
        aligned_ct = sum(1 for x in hs if x.aligned)
        ev_loss = sum(x.ev_loss_bb for x in hs)
        rows.append(LeakRow(
            group_key=key,
            hands=n,
            net_bb=round(net_bb, 4),
            alignment_rate_pct=round(aligned_ct / n * 100, 2),
            ev_loss_bb_sum=round(ev_loss, 4),
        ))

    rows.sort(key=lambda r: r.ev_loss_bb_sum, reverse=True)
    return rows
