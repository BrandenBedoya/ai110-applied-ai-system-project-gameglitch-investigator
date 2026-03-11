#!/usr/bin/env python3
from logic_utils import check_guess, parse_guess, get_range_for_difficulty, update_score

# Test check_guess - the main bug fix
assert check_guess(50, 25) == ('Too High', '📉 Go LOWER!'), "Too High should say Go LOWER"
assert check_guess(10, 25) == ('Too Low', '📈 Go HIGHER!'), "Too Low should say Go HIGHER"
assert check_guess(25, 25) == ('Win', '🎉 Correct!'), "Correct guess"

# Test parse_guess
assert parse_guess('42') == (True, 42, None), "Valid integer"
assert parse_guess('42.5') == (True, 42, None), "Float to int conversion"
assert parse_guess('') == (False, None, "Enter a guess."), "Empty string"
assert parse_guess('abc') == (False, None, "That is not a number."), "Invalid string"

# Test get_range_for_difficulty
assert get_range_for_difficulty('Easy') == (1, 20), "Easy difficulty"
assert get_range_for_difficulty('Normal') == (1, 100), "Normal difficulty"
assert get_range_for_difficulty('Hard') == (1, 50), "Hard difficulty"

# Test update_score
assert update_score(0, 'Win', 1) == 80, "Win on first attempt"
assert update_score(0, 'Too High', 2) == 5, "Too High on even attempt"
assert update_score(0, 'Too High', 3) == -5, "Too High on odd attempt"
assert update_score(0, 'Too Low', 1) == -5, "Too Low penalty"

print("✅ All logic tests passed! Refactoring is successful!")
