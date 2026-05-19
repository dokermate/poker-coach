"""Dataclasses for the GTO advisor engine — no FastAPI/SQLAlchemy deps."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal, Optional


Street = Literal["preflop", "flop", "turn", "river"]
PotType = Literal["srp", "3bp", "4bp"]
HeroRole = Literal["pfr", "caller"]
PreflopSpot = Literal["rfi", "vs_open", "vs_3bet", "vs_4bet"]
Position = Literal["BTN", "CO", "HJ", "LJ", "SB", "BB", "UTG", "UTG1", "UTG2"]
Action = Literal["fold", "check", "call", "bet_33", "bet_66", "bet_100", "raise"]


@dataclass
class SpotInput:
    hero_position: Position
    villain_position: Position
    hero_cards: list[str]          # e.g. ["Ah", "Kd"]
    board: list[str]               # 0 (preflop) to 5 cards
    street: Street
    pot_type: PotType
    hero_role: HeroRole
    preflop_spot: PreflopSpot
    pot_bb: float = 10.0           # pot in bb units
    stack_bb: float = 100.0        # effective stack in bb
    ip: bool = True                # hero is in position?
    mc_iterations: int = 3500


@dataclass
class EVComp:
    action: Action
    ev_bb: float
    size_pct: Optional[float] = None   # fraction of pot for bet actions


@dataclass
class SpotResult:
    recommended_action: Action
    recommended_size: Optional[float]   # fraction of pot, None for check/fold/call
    equity: float                        # hero equity 0-1
    range_advantage: float               # hero range equity - 0.5
    ev_best_bb: float
    ev_comps: list[EVComp]
    mix_json: dict                       # softmax mixing weights
    explanation: str
    disclaimer: str = (
        "⚠️ This advice is based on Monte Carlo simulation and simplified ranges, "
        "NOT a Nash equilibrium solver. Use as a learning guide, not GTO gospel."
    )
