"""
Public API for the gto_advisor package.
"""
from __future__ import annotations
from .models import SpotInput, SpotResult
from .preflop import preflop_advice
from .postflop import postflop_advice


def get_advice(spot: SpotInput) -> SpotResult:
    """
    Route to preflop or postflop advisor based on spot.street.
    This is the single entry point used by the FastAPI service layer.
    """
    if spot.street == "preflop":
        return preflop_advice(
            hero_cards=spot.hero_cards,
            hero_position=spot.hero_position,
            villain_position=spot.villain_position,
            preflop_spot=spot.preflop_spot,
            pot_bb=spot.pot_bb,
            stack_bb=spot.stack_bb,
            mc_iterations=spot.mc_iterations,
        )
    return postflop_advice(spot)
