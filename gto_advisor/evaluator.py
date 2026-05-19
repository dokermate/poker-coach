"""
Pure-Python 7-card hand evaluator (no external dependencies).

Evaluates the best 5-card hand from up to 7 cards.
Higher internal score = better hand.

Card format: rank + suit, e.g. "Ah", "Td", "2c"
Ranks: 2-9, T, J, Q, K, A
Suits: s h d c
"""
from __future__ import annotations
from itertools import combinations

RANK_ORDER = "23456789TJQKA"
RANK_VAL: dict[str, int] = {r: i for i, r in enumerate(RANK_ORDER)}  # 2=0 … A=12

HAND_CLASS = {
    8: "Straight Flush",
    7: "Four of a Kind",
    6: "Full House",
    5: "Flush",
    4: "Straight",
    3: "Three of a Kind",
    2: "Two Pair",
    1: "Pair",
    0: "High Card",
}


def parse_card(card_str: str) -> tuple[int, str]:
    return RANK_VAL[card_str[0].upper()], card_str[1].lower()


def parse_cards(card_strs: list[str]) -> list[tuple[int, str]]:
    return [parse_card(c) for c in card_strs]


def _eval5(hand: list[tuple[int, str]]) -> tuple:
    ranks = sorted([r for r, _ in hand], reverse=True)
    suits = [s for _, s in hand]
    rank_counts: dict[int, int] = {}
    for r in ranks:
        rank_counts[r] = rank_counts.get(r, 0) + 1

    is_flush = len(set(suits)) == 1

    unique_sorted = sorted(set(ranks), reverse=True)
    is_straight = False
    straight_high = 0
    if len(unique_sorted) == 5 and unique_sorted[0] - unique_sorted[4] == 4:
        is_straight = True
        straight_high = unique_sorted[0]
    elif set(unique_sorted) == {12, 3, 2, 1, 0}:
        is_straight = True
        straight_high = 3

    counts = sorted(rank_counts.values(), reverse=True)
    by_count: dict[int, list[int]] = {}
    for r, cnt in rank_counts.items():
        by_count.setdefault(cnt, []).append(r)
    for v in by_count.values():
        v.sort(reverse=True)

    if is_straight and is_flush:
        return (8, straight_high)
    if counts == [4, 1]:
        return (7, by_count[4][0], by_count[1][0])
    if counts == [3, 2]:
        return (6, by_count[3][0], by_count[2][0])
    if is_flush:
        return (5, *ranks)
    if is_straight:
        return (4, straight_high)
    if counts[0] == 3:
        kickers = by_count.get(1, [0, 0])[:2]
        return (3, by_count[3][0], *kickers)
    if counts[:2] == [2, 2]:
        pairs = sorted(by_count[2], reverse=True)
        kicker = by_count[1][0] if by_count.get(1) else 0
        return (2, pairs[0], pairs[1], kicker)
    if counts[0] == 2:
        kickers = by_count.get(1, [0, 0, 0])[:3]
        return (1, by_count[2][0], *kickers)
    return (0, *ranks)


def _best_hand(cards: list[tuple[int, str]]) -> tuple:
    best: tuple = (-1,)
    for combo in combinations(cards, 5):
        score = _eval5(list(combo))
        if score > best:
            best = score
    return best


def evaluate_hand(hole_cards: list[str], board: list[str]) -> tuple:
    """
    Evaluate best 5-card hand from hole+board (3-5 board cards required).
    Returns a comparable tuple where HIGHER = BETTER.
    """
    if len(board) < 3:
        raise ValueError("evaluate_hand requires at least 3 board cards")
    cards = parse_cards(hole_cards + board)
    return _best_hand(cards)


def hand_rank_class(hole_cards: list[str], board: list[str]) -> str:
    score = evaluate_hand(hole_cards, board)
    return HAND_CLASS[score[0]]


def compare_hands(hole1: list[str], hole2: list[str], board: list[str]) -> int:
    """Returns -1 if hole1 wins, 1 if hole2 wins, 0 for tie."""
    s1 = evaluate_hand(hole1, board)
    s2 = evaluate_hand(hole2, board)
    if s1 > s2:
        return -1
    if s1 < s2:
        return 1
    return 0
