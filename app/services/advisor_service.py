"""Service: calls gto_advisor engine, converts to ORM-safe dicts."""
from __future__ import annotations
from gto_advisor import get_advice
from gto_advisor.models import SpotInput


def run_advisor(req) -> dict:
    """
    req: AnalyzeRequest or HandCreate (both share analysis fields).
    Returns a dict ready for API response or Hand ORM row.
    """
    spot = SpotInput(
        hero_position=req.hero_position,
        villain_position=req.villain_position,
        hero_cards=req.hero_cards,
        board=req.board,
        street=req.street,
        pot_type=req.pot_type,
        hero_role=req.hero_role,
        preflop_spot=req.preflop_spot,
        pot_bb=req.pot_bb,
        stack_bb=req.stack_bb,
        ip=req.ip,
        mc_iterations=req.mc_iterations,
    )
    result = get_advice(spot)
    return {
        "recommended_action": result.recommended_action,
        "recommended_size": result.recommended_size,
        "equity": result.equity,
        "range_advantage": result.range_advantage,
        "ev_best_bb": result.ev_best_bb,
        "ev_comps": [vars(c) for c in result.ev_comps],
        "mix_json": result.mix_json,
        "explanation": result.explanation,
        "disclaimer": result.disclaimer,
    }
