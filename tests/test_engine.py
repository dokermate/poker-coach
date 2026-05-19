"""
pytest test suite for poker-coach.
Run: pytest tests/ -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from gto_advisor.evaluator import evaluate_hand, hand_rank_class, compare_hands
from gto_advisor.ranges import expand_range
from gto_advisor.monte_carlo import monte_carlo_equity
from app.services.alignment_service import compute_alignment, session_bonus
from app.services.stats_service import _drawdown


# ── Evaluator ─────────────────────────────────────────────────────────────────

class TestEvaluator:
    def test_royal_flush_beats_straight_flush(self):
        royal = evaluate_hand(["Ah", "Kh"], ["Qh", "Jh", "Th", "2d", "3c"])
        sf = evaluate_hand(["9h", "8h"], ["7h", "6h", "5h", "2d", "3c"])
        assert royal < sf   # lower rank = better in treys

    def test_pair_over_high_card(self):
        pair = evaluate_hand(["As", "Ad"], ["2h", "7c", "Ks", "4d", "9h"])
        high = evaluate_hand(["Ac", "Kd"], ["2h", "7c", "3s", "4d", "9h"])
        assert pair < high

    def test_known_full_house(self):
        cls = hand_rank_class(["Ah", "As"], ["Ad", "Kh", "Ks", "2c", "3d"])
        assert cls == "Full House"

    def test_known_flush(self):
        cls = hand_rank_class(["Ah", "Th"], ["2h", "5h", "8h", "Kd", "3c"])
        assert cls == "Flush"

    def test_compare_hands_win(self):
        result = compare_hands(["Ah", "As"], ["2d", "3c"], ["Kh", "Qs", "Jd", "Ts", "2h"])
        assert result == -1   # hole1 wins

    def test_compare_hands_loss(self):
        result = compare_hands(["2d", "3c"], ["Ah", "As"], ["Kh", "Qs", "Jd", "Ts", "2h"])
        assert result == 1

    def test_minimum_board(self):
        """evaluate_hand must work with exactly 3 board cards."""
        rank = evaluate_hand(["Ah", "Kh"], ["Qh", "Jh", "Th"])
        assert rank > 0


# ── Ranges ────────────────────────────────────────────────────────────────────

class TestRanges:
    def test_pair_combo_count(self):
        combos = expand_range(["AA"])
        assert len(combos) == 6

    def test_suited_combo_count(self):
        combos = expand_range(["AKs"])
        assert len(combos) == 4

    def test_offsuit_combo_count(self):
        combos = expand_range(["AKo"])
        assert len(combos) == 12

    def test_no_suffix_both(self):
        combos = expand_range(["AK"])
        assert len(combos) == 16

    def test_plus_pair(self):
        # QQ+ = QQ, KK, AA = 3 * 6 = 18
        combos = expand_range(["QQ+"])
        assert len(combos) == 18

    def test_plus_suited(self):
        # ATs+ = ATs, AJs, AQs, AKs = 4 * 4 = 16
        combos = expand_range(["ATs+"])
        assert len(combos) == 16

    def test_dedup(self):
        combos = expand_range(["AA", "AA"])
        assert len(combos) == 6

    def test_multi_label(self):
        combos = expand_range(["AA", "KK"])
        assert len(combos) == 12


# ── Monte Carlo ───────────────────────────────────────────────────────────────

class TestMonteCarlo:
    def test_aa_vs_random_preflop(self):
        """AA vs random 2 cards should be ~85% equity."""
        from gto_advisor.ranges import expand_range
        villain = expand_range([
            "22", "33", "44", "55", "66", "77", "88", "99", "TT", "JJ", "QQ", "KK",
            "AKs", "AQs", "AJs", "ATs", "AKo", "AQo",
            "KQs", "QJs", "JTs",
        ])
        eq = monte_carlo_equity(["Ah", "As"], villain, [], iterations=5000, seed=42)
        assert 0.75 <= eq <= 0.95, f"Expected ~85%, got {eq:.2%}"

    def test_nut_flush_draw_on_flop(self):
        """Ah2h vs TP on Kh7h2d: hero has ~35-45% equity."""
        from gto_advisor.ranges import expand_range
        villain = expand_range(["KQs", "KJs", "KTs", "KQo"])
        eq = monte_carlo_equity(["Ah", "2h"], villain, ["Kh", "7h", "2d"], iterations=3000, seed=1)
        assert 0.25 <= eq <= 0.60

    def test_set_vs_flush_draw(self):
        """Set heavily ahead of bare flush draw on flop."""
        from gto_advisor.ranges import expand_range
        villain = expand_range(["Ah2h", "Ah3h", "Ah4h", "Ah5h"])  # these won't expand right
        # Use a realistic villain range for this test
        villain = expand_range(["A2s", "A3s", "A4s", "A5s"])
        eq = monte_carlo_equity(["7h", "7d"], villain, ["7c", "Kh", "2h"], iterations=2000, seed=7)
        # Set is roughly 65%+ favorite
        assert eq >= 0.55


# ── Financial / Net BB ────────────────────────────────────────────────────────

class TestFinancials:
    def test_net_bb_from_net_usd(self):
        bb_usd = 2.0
        net_usd = 10.0
        net_bb = net_usd / bb_usd
        assert net_bb == 5.0

    def test_net_bb_negative(self):
        bb_usd = 0.5
        net_usd = -5.0
        assert net_usd / bb_usd == -10.0

    def test_stack_after_to_net(self):
        stack_before = 200.0
        stack_after = 185.0
        net = stack_after - stack_before
        assert net == -15.0


# ── Alignment ─────────────────────────────────────────────────────────────────

class TestAlignment:
    def _comps(self):
        return [
            {"action": "bet_66", "ev_bb": 3.5},
            {"action": "check",  "ev_bb": 2.8},
            {"action": "fold",   "ev_bb": 0.0},
        ]

    def _mix(self):
        return {"bet_66": 0.70, "check": 0.25, "fold": 0.05}

    def test_exact_best_aligned(self):
        aligned, ev_loss, pts = compute_alignment("bet_66", self._comps(), self._mix())
        assert aligned is True
        assert ev_loss == 0.0
        assert pts == 10

    def test_top2_near_mix_aligned(self):
        aligned, ev_loss, pts = compute_alignment("check", self._comps(), self._mix())
        assert aligned is True
        assert ev_loss == pytest.approx(0.7, abs=0.01)
        # ev_loss > 0.5 → penalty; still aligned
        assert pts == 0  # +5 - 5

    def test_fold_not_aligned(self):
        aligned, ev_loss, pts = compute_alignment("fold", self._comps(), self._mix())
        assert aligned is False
        assert ev_loss == pytest.approx(3.5, abs=0.01)
        assert pts <= -5

    def test_session_bonus_granted(self):
        assert session_bonus(0.75, 25) == 50

    def test_session_bonus_not_enough_hands(self):
        assert session_bonus(0.80, 15) == 0

    def test_session_bonus_low_alignment(self):
        assert session_bonus(0.65, 30) == 0


# ── Drawdown ──────────────────────────────────────────────────────────────────

class TestDrawdown:
    def test_simple_drawdown(self):
        # +10, +5, -20, +3 → peak at 15, trough at -5, drawdown = 20
        dd = _drawdown([10, 5, -20, 3])
        assert dd == 20.0

    def test_no_drawdown(self):
        dd = _drawdown([5, 10, 15, 20])
        assert dd == 0.0

    def test_all_losses(self):
        # peak=0, cumulative hits -15 → drawdown from peak to trough = 15
        dd = _drawdown([-5, -5, -5])
        assert dd == 15.0

    def test_recovery_partial(self):
        # 0→10→5→15→8: peak=15, trough at 8, dd=7
        dd = _drawdown([10, -5, 10, -7])
        assert dd == 7.0
