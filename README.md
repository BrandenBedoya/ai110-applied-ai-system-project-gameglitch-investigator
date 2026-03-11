# 🎮 Game Glitch Investigator: The Impossible Guesser

## 🚨 The Situation

You asked an AI to build a simple "Number Guessing Game" using Streamlit.
It wrote the code, ran away, and now the game is unplayable. 

- You can't win.
- The hints lie to you.
- The secret number seems to have commitment issues.

## 🛠️ Setup

1. Install dependencies: `pip3 install -r requirements.txt`
2. Run the fixed app: `python3 -m streamlit run app.py`
   - Note: Use `python3` on macOS if `python` defaults to Python 2

## 🕵️‍♂️ Your Mission

1. **Play the game.** Open the "Developer Debug Info" tab in the app to see the secret number. Try to win.
2. **Find the State Bug.** Why does the secret number change every time you click "Submit"? Ask ChatGPT: *"How do I keep a variable from resetting in Streamlit when I click a button?"*
3. **Fix the Logic.** The hints ("Higher/Lower") are wrong. Fix them.
4. **Refactor & Test.** - Move the logic into `logic_utils.py`.
   - Run `pytest` in your terminal.
   - Keep fixing until all tests pass!

## 📝 Document Your Experience

✅ **Game's Purpose:** A number-guessing game built with Streamlit where players try to guess a random number within attempts. The game provides hints about whether guesses are too high or too low, with a scoring system based on performance.

✅ **Bugs Found & Fixed:**
1. **Backwards Hint Logic** - When a guess was too high, the game said "Go HIGHER!" (should be "Go LOWER!")
2. **String Conversion Bug** - On even-numbered attempts, the secret was converted to a string, breaking type comparison with integer guesses
3. **Type Mismatch** - Comparing `int` vs `str` caused TypeError that triggered fallback logic with even MORE backwards hints

✅ **Fixes Applied:**
1. Refactored game logic into `logic_utils.py` for separation of concerns
2. Fixed `check_guess()` function to return correct hint messages in all cases
3. Removed buggy string conversion on even attempts
4. Created `test_quick.py` with 7 passing unit tests validating all logic
5. Updated `reflection.md` with detailed AI collaboration documentation

## 📸 Demo

✅ **Game Fixed!** The game now plays correctly:
- Hints are directionally accurate ("Go LOWER!" when guess is too high)
- Secret number remains stable throughout gameplay
- Win condition works properly
- All 7 unit tests pass successfully

**Testing Results:**
```
✅ test_quick.py - 7/7 tests PASSING
✅ Manual gameplay verified
✅ Type safety confirmed (no more string/int comparison errors)
```

## 🚀 Stretch Features

- [ ] Challenge 1: Advanced Edge-Case Testing - Extended test coverage
- [ ] Challenge 4: Enhanced Game UI - Additional UI improvements

## 🤖 AI-Assisted Development

This project was debugged with GitHub Copilot as a teammate:
- **Copilot+ correctly** identified backwards hint logic ✓
- **Copilot+ correctly** refactored code to logic_utils.py with Agent mode ✓
- **Copilot+ misleading** initially on string conversion bug importance

See [reflection.md](reflection.md) for detailed AI collaboration process and lessons learned.
