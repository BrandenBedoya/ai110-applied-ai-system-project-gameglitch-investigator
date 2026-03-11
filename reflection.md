# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

When I first played the game, I guessed the number 1 (with a range of 1-100) and the game told me to "go lower"—which is impossible since 1 is already the minimum. The hints were completely backwards: when my guess was too high, it told me to go higher, and vice versa. Additionally, there was a string conversion bug on even-numbered attempts that was breaking the comparison logic between the guess and the secret number, preventing accurate game feedback.

---

## 2. How did you use AI as a teammate?

I used **GitHub Copilot** (in both inline chat and Agent mode) extensively throughout this project. 

**Correct AI Suggestion:** When I asked Copilot to identify the backwards hint logic, it correctly suggested that the `check_guess()` function had the messages inverted—when `guess > secret`, the condition labeled it "Too High" but the message said "Go HIGHER!" I verified this was correct by playing the game: when I guessed 50 for a secret of 25, the game incorrectly told me to "go higher." Copilot's suggestion led directly to fixing the condition and reversing the hint messages.

**Refactoring with Agent Mode:** Copilot Agent mode successfully moved all four logic functions (`check_guess`, `parse_guess`, `get_range_for_difficulty`, `update_score`) from app.py into logic_utils.py while fixing the backwards hints and updating the imports. I verified this by reviewing the code structure and running test_quick.py—all 7 assertions passed, proving the refactored code worked identically to the original (minus the bug).

**Misleading Suggestion:** Initially, when I asked about the string conversion bug, Copilot wasn't entirely clear about why comparing `int` with `str` breaks Python's comparison operators. Its explanation suggested the bug might be intentional for "edge case handling," which was incorrect. I had to manually test and verify that the string conversion was purely buggy—not a feature—by checking what happens when `42 > "42"` (TypeError). The AI's follow-up explanation after clarification was accurate.

---

## 3. Debugging and testing your fixes

I used a **three-layer testing approach**:

**Manual gameplay testing:** I played the game and confirmed that guessing 1 (the minimum) no longer told me to "go lower." Each guess now displays the correct directional hint.

**Unit testing with test_quick.py:** I created an automated test file that validates all refactored logic functions independently:
- `check_guess(50, 25)` returns `('Too High', '📉 Go LOWER!')` ✓
- `parse_guess('42.5')` correctly converts floats to integers ✓  
- `get_range_for_difficulty()` returns the correct ranges for each difficulty ✓
- `update_score()` applies the correct scoring rules for each outcome ✓

All 7 test cases passed, proving the refactored code maintained the original functionality while fixing the bugs.

**Developer Debug Tab:** The "Developer Debug Info" expander in the Streamlit app showed me the actual secret number, allowing me to verify that my guesses were being compared correctly against it and that the game state remained stable across multiple guesses.

By combining automated tests with manual gameplay verification, I could be confident that the fixes were complete, correct, and didn't introduce new bugs.

---

## 4. What did you learn about Streamlit and state?

The secret number wasn't actually changing on every rerun—the session state was properly initialized and persisted. The real issue was that on even-numbered attempts, the code was converting the secret to a string while the guess remained an integer, causing string comparison instead of numeric comparison, which broke the game logic. Streamlit "reruns" the entire script whenever a user interacts with the app (like clicking a button), but `st.session_state` preserves variables across reruns so the game state persists. I fixed the stability by removing the problematic string conversion and ensuring the secret and guess were always compared as the same type (integers).

---

## 5. Looking ahead: your developer habits

One habit I'm taking forward is **manual testing first, automation second**—before running unit tests, I played the game multiple times and used the debug tab to verify behavior. This helped me catch both bugs immediately. Next time I work with AI on a coding task, I'll be more skeptical of AI-generated logic and trace through the code path myself rather than trusting the implementation—in this case, the backwards hints seemed intentional at first glance but manual testing revealed the problem. This project reinforced that AI-generated code is a starting point, not gospel: even seemingly simple logic like comparison operators can have subtle bugs hiding in plain sight that only become obvious when you actually use the code and verify it works the way you expect.


