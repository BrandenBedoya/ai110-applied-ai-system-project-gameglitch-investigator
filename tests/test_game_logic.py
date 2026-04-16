"""
Unit tests for game logic (src/game/logic_utils.py).

Preserved from Module 1 and extended with regression tests for the
bugs identified and fixed in that module.
"""
import pytest
from src.game.logic_utils import (
    check_guess,
    get_range_for_difficulty,
    parse_guess,
    update_score,
)


class TestGetRangeForDifficulty:
    def test_easy(self):
        assert get_range_for_difficulty("Easy") == (1, 20)

    def test_normal(self):
        assert get_range_for_difficulty("Normal") == (1, 100)

    def test_hard(self):
        assert get_range_for_difficulty("Hard") == (1, 50)

    def test_unknown_falls_back_to_normal(self):
        assert get_range_for_difficulty("Impossible") == (1, 100)


class TestParseGuess:
    def test_valid_integer(self):
        ok, val, err = parse_guess("42")
        assert ok is True
        assert val == 42
        assert err is None

    def test_empty_string(self):
        ok, val, err = parse_guess("")
        assert ok is False
        assert val is None

    def test_whitespace_only(self):
        ok, _, _ = parse_guess("   ")
        assert ok is False

    def test_none_input(self):
        ok, _, _ = parse_guess(None)
        assert ok is False

    def test_word_input(self):
        ok, _, _ = parse_guess("fifty")
        assert ok is False

    def test_float_is_truncated_to_int(self):
        ok, val, _ = parse_guess("7.9")
        assert ok is True
        assert val == 7

    def test_negative_number_accepted(self):
        ok, val, _ = parse_guess("-3")
        assert ok is True
        assert val == -3


class TestCheckGuess:
    def test_exact_match_returns_win(self):
        outcome, _ = check_guess(50, 50)
        assert outcome == "Win"

    def test_too_high_outcome(self):
        outcome, _ = check_guess(75, 50)
        assert outcome == "Too High"

    def test_too_low_outcome(self):
        outcome, _ = check_guess(25, 50)
        assert outcome == "Too Low"

    # ── Regression: Module 1 Bug #1 — hints were backwards ────────────────

    def test_hint_not_backwards_when_guess_too_high(self):
        """If guess > secret, hint must say LOWER, not HIGHER."""
        _, msg = check_guess(99, 1)
        assert "LOWER" in msg.upper(), f"Expected LOWER in hint, got: {msg!r}"

    def test_hint_not_backwards_when_guess_too_low(self):
        """If guess < secret, hint must say HIGHER, not LOWER."""
        _, msg = check_guess(1, 99)
        assert "HIGHER" in msg.upper(), f"Expected HIGHER in hint, got: {msg!r}"


class TestUpdateScore:
    def test_win_adds_points(self):
        score = update_score(0, "Win", attempt_number=1)
        assert score > 0

    def test_win_earlier_scores_higher(self):
        early = update_score(0, "Win", attempt_number=1)
        late = update_score(0, "Win", attempt_number=9)
        assert early > late

    def test_win_minimum_points_is_ten(self):
        score = update_score(0, "Win", attempt_number=100)
        assert score >= 10

    def test_wrong_guess_subtracts_points(self):
        score = update_score(50, "Too Low", attempt_number=3)
        assert score < 50

    def test_score_never_goes_below_zero(self):
        score = update_score(0, "Too Low", attempt_number=1)
        assert score >= 0, "Score floor should be 0"

    def test_unknown_outcome_returns_unchanged_score(self):
        score = update_score(42, "Unknown", attempt_number=1)
        assert score == 42
