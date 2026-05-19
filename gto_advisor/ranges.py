"""
Range utilities: expand shorthand labels (AKs, QQ, ATo+) into individual combos.

Combo format: two card strings, e.g. ("Ah", "Kh").
RANKS = "AKQJT98765432"  (index 0=A, highest … 12=2, lowest)
"""
from __future__ import annotations
import itertools
import random

RANKS = "AKQJT98765432"
SUITS = "shdc"


def _rank_idx(r: str) -> int:
    """Lower index = higher rank. A=0, K=1, ... 2=12."""
    return RANKS.index(r.upper())


def _rank_combos(r1: str, r2: str, suited: bool) -> list[tuple[str, str]]:
    """All combos of rank r1+r2. r1==r2 means pair (C(4,2)=6 combos)."""
    combos: list[tuple[str, str]] = []
    if r1 == r2:
        for s1, s2 in itertools.combinations(SUITS, 2):
            combos.append((f"{r1}{s1}", f"{r2}{s2}"))
    elif suited:
        for s in SUITS:
            combos.append((f"{r1}{s}", f"{r2}{s}"))
    else:
        for s1 in SUITS:
            for s2 in SUITS:
                if s1 != s2:
                    combos.append((f"{r1}{s1}", f"{r2}{s2}"))
    return combos


def _expand_one(label: str) -> list[tuple[str, str]]:
    """Expand a single label like 'AKs', 'QQ', 'ATo+', 'JJ+' into combos."""
    label = label.strip()

    plus = label.endswith("+")
    if plus:
        label = label[:-1]

    # Detect suited / offsuit suffix
    if label.endswith("s"):
        suited_only = True
        offsuit_only = False
        label = label[:-1]
    elif label.endswith("o"):
        suited_only = False
        offsuit_only = True
        label = label[:-1]
    else:
        suited_only = False
        offsuit_only = False

    if len(label) != 2:
        return []

    r1, r2 = label[0].upper(), label[1].upper()

    # --- Pair ---
    if r1 == r2:
        if plus:
            # JJ+ = JJ, QQ, KK, AA → all pairs with idx <= _rank_idx(r1)
            combos = []
            for i in range(_rank_idx(r1) + 1):  # 0=A … idx(r1)
                combos.extend(_rank_combos(RANKS[i], RANKS[i], False))
            return combos
        return _rank_combos(r1, r2, False)

    # --- Non-pair ---
    # Ensure r1 is the higher rank (lower index)
    if _rank_idx(r1) > _rank_idx(r2):
        r1, r2 = r2, r1  # swap so r1=higher

    def build(kicker: str) -> list[tuple[str, str]]:
        if suited_only:
            return _rank_combos(r1, kicker, True)
        if offsuit_only:
            return _rank_combos(r1, kicker, False)
        return _rank_combos(r1, kicker, True) + _rank_combos(r1, kicker, False)

    if plus:
        # ATs+ → kicker moves from T up toward (but not including) A
        # i.e. indices from _rank_idx(r2) down to _rank_idx(r1)+1
        combos = []
        for i in range(_rank_idx(r2), _rank_idx(r1), -1):  # r2 idx down to r1+1
            combos.extend(build(RANKS[i]))
        return combos

    return build(r2)


def expand_range(labels: list[str]) -> list[tuple[str, str]]:
    """Expand a list of range labels into unique combos."""
    seen: set[frozenset[str]] = set()
    result: list[tuple[str, str]] = []
    for label in labels:
        for combo in _expand_one(label):
            key = frozenset(combo)
            if key not in seen:
                seen.add(key)
                result.append(combo)
    return result


def remove_blockers(
    combos: list[tuple[str, str]],
    dead_cards: list[str],
) -> list[tuple[str, str]]:
    """Filter out combos that contain any card in dead_cards."""
    dead = set(dead_cards)
    return [c for c in combos if c[0] not in dead and c[1] not in dead]


def sample_range(
    combos: list[tuple[str, str]],
    n: int,
    rng: random.Random | None = None,
) -> list[tuple[str, str]]:
    """Sample up to n combos uniformly."""
    if rng is None:
        rng = random.Random()
    if len(combos) <= n:
        return list(combos)
    return rng.sample(combos, n)
