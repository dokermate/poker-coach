"""
Postflop advisor using EV models for bet/check decisions.

EV models (simplified, educational):
  evBet(size) = fold_equity * pot + (1-fold_equity) * equity * (pot+size) - (1-fold_equity)*(1-equity)*size
  evCheck = equity * pot * realization_factor  (IP realization > OOP)
"""
from __future__ import annotations
from math import exp
from .models import SpotInput, SpotResult, EVComp, Action
from .ranges import expand_range
from .monte_carlo import monte_carlo_equity, range_equity

# Simplified villain ranges for postflop (continuation)
_POSTFLOP_VILLAIN_RANGE = [
    "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77",
    "AKs", "AQs", "AJs", "ATs", "AKo", "AQo",
    "KQs", "KJs", "QJs", "JTs", "T9s", "98s", "87s", "76s", "65s",
    "A5s", "A4s", "A3s", "A2s",
]

# Sizing options: fraction of pot
BET_SIZES: dict[Action, float] = {
    "bet_33": 0.33,
    "bet_66": 0.66,
    "bet_100": 1.00,
}


def _fold_equity(bet_fraction: float, street: str) -> float:
    """
    Heuristic fold equity based on bet size and street.
    Smaller bets get called more; later streets fold more.
    """
    street_factor = {"flop": 0.9, "turn": 1.0, "river": 1.1}.get(street, 1.0)
    # Base fold % modeled on typical population tendencies
    base = 0.25 + bet_fraction * 0.30
    return min(base * street_factor, 0.70)


def _realization_factor(ip: bool, pot_type: str) -> float:
    """IP has better realization of equity; 3bp/4bp less realization OOP."""
    base = 0.85 if ip else 0.70
    if pot_type in ("3bp", "4bp"):
        base -= 0.05
    return base


def ev_bet(equity: float, pot_bb: float, bet_bb: float, fold_eq: float) -> float:
    ev_fold_outcome = fold_eq * pot_bb
    ev_showdown = (1 - fold_eq) * (equity * (pot_bb + bet_bb) - (1 - equity) * bet_bb)
    return ev_fold_outcome + ev_showdown


def ev_check(equity: float, pot_bb: float, realization: float) -> float:
    return equity * pot_bb * realization


def postflop_advice(spot: SpotInput) -> SpotResult:
    # --- Build villain range ---
    villain_combos = expand_range(_POSTFLOP_VILLAIN_RANGE)

    # --- Hero equity vs villain range ---
    equity = monte_carlo_equity(
        spot.hero_cards, villain_combos, spot.board, iterations=spot.mc_iterations
    )

    # --- Range advantage ---
    hero_range_labels = _POSTFLOP_VILLAIN_RANGE  # simplified: same range shape
    hero_combos = expand_range(hero_range_labels)
    range_adv = range_equity(
        hero_combos, villain_combos, spot.board,
        sample_n=40, iterations_per_combo=150
    ) - 0.5

    pot = spot.pot_bb
    realization = _realization_factor(spot.ip, spot.pot_type)

    # --- EV for each action ---
    ev_comps: list[EVComp] = []

    # Check / call
    ev_chk = ev_check(equity, pot, realization)
    ev_comps.append(EVComp("check", round(ev_chk, 3), None))

    # Bet sizes
    for action, frac in BET_SIZES.items():
        bet_bb = pot * frac
        fold_eq = _fold_equity(frac, spot.street)
        ev = ev_bet(equity, pot, bet_bb, fold_eq)
        ev_comps.append(EVComp(action, round(ev, 3), frac))

    # Fold (0 EV baseline)
    ev_comps.append(EVComp("fold", 0.0, None))

    best = max(ev_comps, key=lambda x: x.ev_bb)

    # --- Softmax mixing ---
    evs = [c.ev_bb for c in ev_comps]
    max_ev = max(evs)
    exps = [exp(e - max_ev) for e in evs]
    total = sum(exps)
    mix = {c.action: round(e / total, 3) for c, e in zip(ev_comps, exps)}

    # --- Natural language explanation ---
    pos_str = "IP (in position)" if spot.ip else "OOP (out of position)"
    ra_str = f"{range_adv:+.0%}"
    if equity > 0.60 and range_adv > 0.05:
        txt = (
            f"Strong equity ({equity:.0%}) with range advantage ({ra_str}) {pos_str}. "
            f"Betting for value is clearly best. "
            f"Larger sizing ({best.recommended_size:.0%} pot) punishes weak draws."
            if best.action != "check" else
            f"Good equity ({equity:.0%}) {pos_str}. Check-raise or slow-play may apply."
        )
    elif equity < 0.40 and range_adv < -0.05:
        txt = (
            f"Low equity ({equity:.0%}) with range disadvantage ({ra_str}). "
            f"Checking/folding to pressure is advisable. Bluffing has low fold equity here."
        )
    else:
        txt = (
            f"Equity: {equity:.0%} | Range advantage: {ra_str} | {pos_str}. "
            f"Mixed strategy suggested. "
            f"Best action by EV: {best.action} (EV {best.ev_bb:+.2f}bb). "
            f"Consider your overall range balance."
        )

    return SpotResult(
        recommended_action=best.action,
        recommended_size=best.size_pct,
        equity=round(equity, 4),
        range_advantage=round(range_adv, 4),
        ev_best_bb=round(best.ev_bb, 3),
        ev_comps=ev_comps,
        mix_json=mix,
        explanation=txt,
    )
