"""
Monte Carlo equity calculator — pure Python, no external deps.
"""
from __future__ import annotations
import random

from .evaluator import compare_hands
from .ranges import remove_blockers, sample_range

RANKS = "AKQJT98765432"
SUITS = "shdc"
ALL_CARD_STRS: list[str] = [f"{r}{s}" for r in RANKS for s in SUITS]


def _runout(board, hero, villain, rng):
    used = set(board + hero + villain)
    deck = [c for c in ALL_CARD_STRS if c not in used]
    need = 5 - len(board)
    full_board = board + rng.sample(deck, need) if need > 0 else board
    result = compare_hands(hero, villain, full_board)
    return 1.0 if result == -1 else (0.0 if result == 1 else 0.5)


def monte_carlo_equity(hero_cards, villain_combos, board, iterations=3500, seed=None):
    rng = random.Random(seed)
    dead = hero_cards + board
    available = remove_blockers(villain_combos, dead)
    if not available:
        return 0.5
    total = sum(_runout(board, hero_cards, list(rng.choice(available)), rng) for _ in range(iterations))
    return total / iterations


def range_equity(hero_combos, villain_combos, board, sample_n=30, iterations_per_combo=100, seed=None):
    rng = random.Random(seed)
    dead = board
    hero_sample = remove_blockers(hero_combos, dead)
    if not hero_sample:
        return 0.5
    hero_sample = sample_range(hero_sample, sample_n, rng)
    eqs = []
    for hero_combo in hero_sample:
        va = remove_blockers(villain_combos, list(hero_combo) + dead)
        eq = monte_carlo_equity(list(hero_combo), va or villain_combos, board,
                                 iterations=iterations_per_combo, seed=rng.randint(0, 2**31))
        eqs.append(eq)
    return sum(eqs) / len(eqs)
