"""
SQLAlchemy 2 ORM models.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer, String, Text, JSON,
    Enum as SAEnum,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    total_points: Mapped[int] = mapped_column(Integer, default=0)
    lifetime_pnl_usd: Mapped[float] = mapped_column(Float, default=0.0)

    tables: Mapped[list["Table"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    sessions: Mapped[list["GameSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Table(Base):
    __tablename__ = "tables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    sb_usd: Mapped[float] = mapped_column(Float, nullable=False)
    bb_usd: Mapped[float] = mapped_column(Float, nullable=False)
    ante_usd: Mapped[float] = mapped_column(Float, default=0.0)
    game_type: Mapped[str] = mapped_column(SAEnum("cash", "mtt", name="game_type_enum"), default="cash")
    max_players: Mapped[int] = mapped_column(Integer, default=6)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    owner: Mapped["User"] = relationship(back_populates="tables")
    sessions: Mapped[list["GameSession"]] = relationship(back_populates="table")


class GameSession(Base):
    __tablename__ = "game_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    table_id: Mapped[int] = mapped_column(ForeignKey("tables.id"), nullable=False)
    start_stack_usd: Mapped[float] = mapped_column(Float, nullable=False)
    start_stack_bb: Mapped[float] = mapped_column(Float, nullable=False)
    current_stack_usd: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(
        SAEnum("active", "completed", name="session_status_enum"), default="active"
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="sessions")
    table: Mapped["Table"] = relationship(back_populates="sessions")
    hands: Mapped[list["Hand"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    rebuys: Mapped[list["Rebuy"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class Hand(Base):
    __tablename__ = "hands"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("game_sessions.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    played_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    # Poker fields
    hero_position: Mapped[str] = mapped_column(String(10), nullable=False)
    villain_position: Mapped[str] = mapped_column(String(10), nullable=False)
    hero_cards: Mapped[str] = mapped_column(String(20), nullable=False)   # JSON "Ah,Kd"
    board: Mapped[str] = mapped_column(String(30), default="")             # JSON "As,Ks,Qs"
    street: Mapped[str] = mapped_column(String(10), nullable=False)
    pot_type: Mapped[str] = mapped_column(String(5), nullable=False)
    hero_role: Mapped[str] = mapped_column(String(10), nullable=False)
    preflop_spot: Mapped[str] = mapped_column(String(10), nullable=False)
    pot_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Advisor output (stored for alignment calc)
    recommended_action: Mapped[str] = mapped_column(String(20), nullable=False)
    recommended_size: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    equity: Mapped[float] = mapped_column(Float, nullable=False)
    ev_best_bb: Mapped[float] = mapped_column(Float, nullable=False)
    ev_comps_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    mix_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    # User decision
    user_action: Mapped[str] = mapped_column(String(20), nullable=False)

    # Financial result
    stack_before_usd: Mapped[float] = mapped_column(Float, nullable=False)
    stack_after_usd: Mapped[float] = mapped_column(Float, nullable=False)
    net_usd: Mapped[float] = mapped_column(Float, nullable=False)
    net_bb: Mapped[float] = mapped_column(Float, nullable=False)

    # Alignment
    aligned: Mapped[bool] = mapped_column(Boolean, default=False)
    ev_loss_bb: Mapped[float] = mapped_column(Float, default=0.0)
    points_earned: Mapped[int] = mapped_column(Integer, default=0)

    session: Mapped["GameSession"] = relationship(back_populates="hands")


class Rebuy(Base):
    """Phase 2: Track rebuys without creating a hand."""
    __tablename__ = "rebuys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("game_sessions.id"), nullable=False)
    rebuy_usd: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    session: Mapped["GameSession"] = relationship(back_populates="rebuys")
