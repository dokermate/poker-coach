"""Pydantic v2 request/response schemas."""
from __future__ import annotations
from datetime import datetime
from typing import Any, Literal, Optional
from pydantic import BaseModel, EmailStr, field_validator


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    total_points: int
    lifetime_pnl_usd: float
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Tables ────────────────────────────────────────────────────────────────────

class TableCreate(BaseModel):
    name: str
    sb_usd: float
    bb_usd: float
    ante_usd: float = 0.0
    game_type: Literal["cash", "mtt"] = "cash"
    max_players: Literal[6, 9] = 6


class TableOut(BaseModel):
    id: int
    name: str
    sb_usd: float
    bb_usd: float
    ante_usd: float
    game_type: str
    max_players: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Sessions ──────────────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    table_id: int
    start_stack_usd: float


class SessionOut(BaseModel):
    id: int
    table_id: int
    start_stack_usd: float
    start_stack_bb: float
    current_stack_usd: float
    status: str
    started_at: datetime
    ended_at: Optional[datetime]

    model_config = {"from_attributes": True}


# ── Hands ─────────────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    hero_position: str
    villain_position: str
    hero_cards: list[str]   # ["Ah", "Kd"]
    board: list[str] = []
    street: Literal["preflop", "flop", "turn", "river"] = "preflop"
    pot_type: Literal["srp", "3bp", "4bp"] = "srp"
    hero_role: Literal["pfr", "caller"] = "pfr"
    preflop_spot: Literal["rfi", "vs_open", "vs_3bet", "vs_4bet"] = "rfi"
    pot_bb: float = 10.0
    stack_bb: float = 100.0
    mc_iterations: int = 3500
    ip: bool = True

    @field_validator("hero_cards")
    @classmethod
    def two_cards(cls, v: list[str]) -> list[str]:
        if len(v) != 2:
            raise ValueError("hero_cards must have exactly 2 cards")
        return v


class AdvisorOut(BaseModel):
    recommended_action: str
    recommended_size: Optional[float]
    equity: float
    range_advantage: float
    ev_best_bb: float
    ev_comps: list[dict]
    mix_json: dict
    explanation: str
    disclaimer: str


class HandCreate(BaseModel):
    session_id: int
    # poker fields
    hero_position: str
    villain_position: str
    hero_cards: list[str]
    board: list[str] = []
    street: Literal["preflop", "flop", "turn", "river"] = "preflop"
    pot_type: Literal["srp", "3bp", "4bp"] = "srp"
    hero_role: Literal["pfr", "caller"] = "pfr"
    preflop_spot: Literal["rfi", "vs_open", "vs_3bet", "vs_4bet"] = "rfi"
    pot_usd: Optional[float] = None
    pot_bb: float = 10.0
    stack_bb: float = 100.0
    ip: bool = True
    mc_iterations: int = 3500
    # user decision
    user_action: str
    # financial result — provide one of two:
    net_usd: Optional[float] = None
    stack_after_usd: Optional[float] = None

    @field_validator("hero_cards")
    @classmethod
    def two_cards(cls, v: list[str]) -> list[str]:
        if len(v) != 2:
            raise ValueError("hero_cards must have exactly 2 cards")
        return v


class HandOut(BaseModel):
    id: int
    session_id: int
    played_at: datetime
    hero_position: str
    villain_position: str
    hero_cards: str
    board: str
    street: str
    recommended_action: str
    user_action: str
    net_usd: float
    net_bb: float
    aligned: bool
    ev_loss_bb: float
    points_earned: int
    equity: float
    ev_best_bb: float
    explanation: str

    model_config = {"from_attributes": True}


# ── Stats ─────────────────────────────────────────────────────────────────────

class StatsSummary(BaseModel):
    hands_played: int
    session_pnl_usd: float
    session_pnl_bb: float
    roi_session_pct: float
    bb_per_100: float
    lifetime_pnl_usd: float
    alignment_rate_pct: float
    ev_loss_bb_total: float
    total_points: int
    max_drawdown_usd: float
    max_drawdown_bb: float


class EquityCurvePoint(BaseModel):
    played_at: datetime
    cumulative_pnl_usd: float
    current_stack_usd: float


class LeakRow(BaseModel):
    group_key: str
    hands: int
    net_bb: float
    alignment_rate_pct: float
    ev_loss_bb_sum: float


class RebuyCreate(BaseModel):
    session_id: int
    rebuy_usd: float
