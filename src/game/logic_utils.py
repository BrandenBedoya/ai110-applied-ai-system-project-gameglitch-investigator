"""
Game logic for Glitchy Guesser.

Preserved from Module 1 with one improvement: score is now floored at 0
to prevent negative scores (known issue bp-010 in the knowledge base).
"""
from __future__ import annotations  # PEP 563 — lets 'str | None' work on Python 3.9


def get_range_for_difficulty(difficulty: str) -> tuple[int, int]:
    """Return (low, high) inclusive range for a given difficulty."""
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 100
    if difficulty == "Hard":
        return 1, 50
    return 1, 100


def parse_guess(raw: str | None) -> tuple[bool, int | None, str | None]:
    """
    Parse user input into an integer guess.

    Returns: (ok, guess_int, error_message)
    """
    if raw is None or raw.strip() == "":
        return False, None, "Enter a guess."

    try:
        value = int(float(raw)) if "." in raw else int(raw)
    except (ValueError, TypeError):
        return False, None, "That is not a number."

    return True, value, None


def check_guess(guess: int, secret: int) -> tuple[str, str]:
    """
    Compare guess to secret and return (outcome, hint_message).

    Bug fixed in Module 1: hint messages were originally backwards.
    If guess > secret → "Go LOWER!" (not HIGHER).
    """
    if guess == secret:
        return "Win", "Correct!"

    try:
        if guess > secret:
            return "Too High", "Go LOWER!"
        return "Too Low", "Go HIGHER!"
    except TypeError:
        # Fallback for unexpected type mismatch
        g = str(guess)
        s = str(secret)
        if g == s:
            return "Win", "Correct!"
        if g > s:
            return "Too High", "Go LOWER!"
        return "Too Low", "Go HIGHER!"


def update_score(current_score: int, outcome: str, attempt_number: int) -> int:
    """
    Update score based on outcome and attempt number.

    Improvement over Module 1: score is floored at 0 (cannot go negative).
    """
    if outcome == "Win":
        points = max(10, 100 - 10 * attempt_number)
        return current_score + points

    if outcome in ("Too High", "Too Low"):
        penalty = 5
        return max(0, current_score - penalty)

    return current_score
