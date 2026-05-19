"""
Alignment rules:
  best_action = argmax EV from ev_comps
  aligned if:
    user_action == best_action
    OR user_action is in top-2 mix labels AND ev within 0.15bb of best
Points:
  +10 aligned best, +5 near-mix, -5 if ev_loss_bb > 0.5, +50 session bonus
"""
from __future__ import annotations

EV_NEAR_THRESHOLD = 0.15   # bb


def compute_alignment(
    user_action: str,
    ev_comps: list[dict],   # list of {action, ev_bb, ...}
    mix_json: dict,
) -> tuple[bool, float, int]:
    """
    Returns (aligned, ev_loss_bb, points_earned).
    """
    if not ev_comps:
        return False, 0.0, 0

    sorted_comps = sorted(ev_comps, key=lambda x: x["ev_bb"], reverse=True)
    best = sorted_comps[0]
    best_ev = best["ev_bb"]

    # User's EV
    user_ev = next((c["ev_bb"] for c in ev_comps if c["action"] == user_action), None)
    if user_ev is None:
        # action not in comps → treated as fold
        user_ev = 0.0

    ev_loss = max(best_ev - user_ev, 0.0)

    # Top-2 mix by weight
    top2_mix = sorted(mix_json.items(), key=lambda x: x[1], reverse=True)[:2]
    top2_labels = {a for a, _ in top2_mix}

    aligned = False
    if user_action == best["action"]:
        aligned = True
        points = 10
    elif user_action in top2_labels and ev_loss <= EV_NEAR_THRESHOLD:
        aligned = True
        points = 5
    else:
        points = 0

    # Penalty
    if ev_loss > 0.5:
        points -= 5

    return aligned, round(ev_loss, 4), points


def session_bonus(alignment_rate: float, hands: int) -> int:
    """Returns +50 if alignment >= 70% and hands >= 20."""
    if hands >= 20 and alignment_rate >= 0.70:
        return 50
    return 0
