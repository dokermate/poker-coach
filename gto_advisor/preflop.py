"""
Preflop range library and advice engine.

Ranges are stored as lists of label strings. expand_range() converts them to combos.
These are simplified, reasonable ranges — NOT solver-derived.
"""
from __future__ import annotations
from .models import Position, PotType, HeroRole, PreflopSpot, Action, EVComp, SpotResult
from .ranges import expand_range
from .monte_carlo import monte_carlo_equity, range_equity

# ---------------------------------------------------------------------------
# Range library
# ---------------------------------------------------------------------------

# RFI ranges per position (open-raise first-in)
RFI_RANGES: dict[str, list[str]] = {
    "BTN": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
            "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
            "AKo", "AQo", "AJo", "ATo", "A9o",
            "KQs", "KJs", "KTs", "K9s", "K8s", "K7s", "K6s",
            "KQo", "KJo", "KTo",
            "QJs", "QTs", "Q9s", "Q8s", "QJo", "QTo",
            "JTs", "J9s", "J8s", "JTo",
            "T9s", "T8s", "T7s", "98s", "97s", "87s", "86s", "76s", "75s", "65s", "54s"],
    "CO": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33",
            "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s",
            "AKo", "AQo", "AJo", "ATo",
            "KQs", "KJs", "KTs", "K9s", "K8s", "KQo", "KJo",
            "QJs", "QTs", "Q9s", "QJo",
            "JTs", "J9s", "T9s", "T8s", "98s", "87s", "76s", "65s", "54s"],
    "HJ": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44",
            "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s",
            "AKo", "AQo", "AJo",
            "KQs", "KJs", "KTs", "K9s", "KQo", "KJo",
            "QJs", "QTs", "Q9s", "QJo",
            "JTs", "J9s", "T9s", "T8s", "98s", "87s", "76s", "65s"],
    "UTG": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77",
            "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A5s",
            "AKo", "AQo", "AJo",
            "KQs", "KJs", "KTs", "KQo",
            "QJs", "QTs", "JTs", "T9s", "98s", "87s"],
    "SB": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
            "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
            "AKo", "AQo", "AJo", "ATo", "A9o", "A8o",
            "KQs", "KJs", "KTs", "K9s", "K8s", "K7s",
            "KQo", "KJo", "KTo",
            "QJs", "QTs", "Q9s", "QJo",
            "JTs", "J9s", "T9s", "T8s", "98s", "87s", "76s", "65s", "54s"],
}
# Fallback for positions not listed
RFI_RANGES["LJ"] = RFI_RANGES["HJ"]
RFI_RANGES["UTG1"] = RFI_RANGES["UTG"]
RFI_RANGES["UTG2"] = RFI_RANGES["UTG"]
RFI_RANGES["BB"] = RFI_RANGES["BTN"]  # BB steal (unlikely, but safe fallback)

# BB defend vs BTN open (call range)
BB_DEFEND_VS_BTN: list[str] = [
    "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
    "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
    "AKo", "AQo", "AJo", "ATo", "A9o", "A8o", "A7o", "A6o", "A5o",
    "KQs", "KJs", "KTs", "K9s", "K8s", "K7s", "K6s", "K5s", "K4s", "K3s", "K2s",
    "KQo", "KJo", "KTo", "K9o",
    "QJs", "QTs", "Q9s", "Q8s", "Q7s", "Q6s", "QJo", "QTo",
    "JTs", "J9s", "J8s", "J7s", "JTo",
    "T9s", "T8s", "T7s", "T6s", "98s", "97s", "96s", "87s", "86s", "76s", "75s", "65s", "64s", "54s", "53s",
]

# 3bet ranges (hero 3bets vs open)
THREEB_RANGE: dict[str, list[str]] = {
    "BTN": ["AA", "KK", "QQ", "JJ", "TT", "AKs", "AQs", "AJs", "AKo", "AQo",
            "A5s", "A4s", "KQs", "QJs"],
    "BB": ["AA", "KK", "QQ", "JJ", "TT", "AKs", "AQs", "AJs", "AKo", "AQo", "AJo",
           "A5s", "A4s", "A3s", "KQs", "KJs", "QJs", "JTs"],
    "SB": ["AA", "KK", "QQ", "JJ", "AKs", "AQs", "AKo", "A5s", "A4s", "KQs"],
}
# Fallback
for _pos in ["CO", "HJ", "LJ", "UTG", "UTG1", "UTG2"]:
    THREEB_RANGE[_pos] = ["AA", "KK", "QQ", "JJ", "AKs", "AQs", "AKo", "A5s", "KQs"]

# 4bet ranges
FOURB_RANGE: list[str] = ["AA", "KK", "QQ", "AKs", "AKo", "A5s"]

# Villain call/continue range vs 3bet (simplified, used as villain range in MC)
CALL_VS_3B: list[str] = ["QQ", "JJ", "TT", "99", "AKs", "AQs", "AJs", "AKo", "AQo",
                          "KQs", "KJs", "QJs", "JTs"]


def _villain_range(spot: PreflopSpot, villain_pos: str) -> list[str]:
    if spot == "rfi":
        return RFI_RANGES.get(villain_pos, RFI_RANGES["CO"])
    if spot == "vs_open":
        return RFI_RANGES.get(villain_pos, RFI_RANGES["BTN"])
    if spot == "vs_3bet":
        return CALL_VS_3B
    return FOURB_RANGE  # vs_4bet


def preflop_advice(
    hero_cards: list[str],
    hero_position: str,
    villain_position: str,
    preflop_spot: PreflopSpot,
    pot_bb: float = 3.0,
    stack_bb: float = 100.0,
    mc_iterations: int = 3500,
) -> SpotResult:
    from math import exp

    villain_labels = _villain_range(preflop_spot, villain_position)
    villain_combos = expand_range(villain_labels)

    equity = monte_carlo_equity(hero_cards, villain_combos, [], iterations=mc_iterations)

    # Simple EV model preflop
    # ev_raise = equity*(pot+raise) - (1-equity)*raise  (fold equity ignored, simplified)
    raise_size_bb = pot_bb * 2.5 if preflop_spot == "rfi" else pot_bb
    ev_raise = equity * (pot_bb + raise_size_bb) - (1 - equity) * raise_size_bb
    ev_call = equity * pot_bb * 2 - (1 - equity) * pot_bb
    ev_fold = 0.0

    comps = [
        EVComp("raise", round(ev_raise, 3)),
        EVComp("call", round(ev_call, 3)),
        EVComp("fold", ev_fold),
    ]
    best = max(comps, key=lambda x: x.ev_bb)

    # Softmax mix
    evs = [c.ev_bb for c in comps]
    max_ev = max(evs)
    exps = [exp(e - max_ev) for e in evs]
    total = sum(exps)
    mix = {c.action: round(e / total, 3) for c, e in zip(comps, exps)}

    # Human explanation
    if equity >= 0.60:
        explanation = (
            f"Strong hand ({equity:.0%} equity vs villain range). "
            f"Raising for value is recommended."
        )
    elif equity >= 0.48:
        explanation = (
            f"Marginal spot ({equity:.0%} equity). Consider pot type, position, and stack depth. "
            f"A mix of raise/call may be optimal."
        )
    else:
        explanation = (
            f"Weak equity ({equity:.0%}) vs villain's range. Folding or calling in position only."
        )

    return SpotResult(
        recommended_action=best.action,
        recommended_size=raise_size_bb if best.action == "raise" else None,
        equity=round(equity, 4),
        range_advantage=round(equity - 0.5, 4),
        ev_best_bb=round(best.ev_bb, 3),
        ev_comps=comps,
        mix_json=mix,
        explanation=explanation,
    )
