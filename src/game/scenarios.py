"""
Pre-written buggy code scenarios for demo and reliability testing.

Each scenario has:
  - id, name, description
  - buggy_code: the snippet to submit to the agent
  - expected_bug_type: category the agent should identify
  - expected_keywords: words that should appear in a correct analysis
"""

SCENARIOS: list[dict] = [
    {
        "id": "scenario-001",
        "name": "Backwards Hint Logic",
        "description": "Hint messages are reversed — Go HIGHER when guess is too high.",
        "buggy_code": """\
def check_guess(guess, secret):
    if guess == secret:
        return "Win", "Correct!"
    if guess > secret:
        # BUG: tells the player to go higher when they should go lower
        return "Too High", "Go HIGHER!"
    else:
        return "Too Low", "Go LOWER!"
""",
        "expected_bug_type": "logic_error",
        "expected_keywords": ["backwards", "reversed", "lower", "hint"],
    },
    {
        "id": "scenario-002",
        "name": "State Not Initialized with Guard",
        "description": "session_state.secret resets on every Streamlit rerun.",
        "buggy_code": """\
import streamlit as st
import random

# BUG: no 'if key not in st.session_state' guard
# This runs on EVERY rerun, resetting the secret each time
st.session_state.secret = random.randint(1, 100)
st.session_state.attempts = 0

guess = st.text_input("Guess a number (1-100):")
if st.button("Submit"):
    if int(guess) == st.session_state.secret:
        st.success("Correct!")
    else:
        st.error("Wrong! Try again.")
""",
        "expected_bug_type": "state_management",
        "expected_keywords": ["session_state", "initialization", "rerun", "reset"],
    },
    {
        "id": "scenario-003",
        "name": "Type Mismatch in Comparison",
        "description": "Comparing a str guess to an int secret causes TypeError in Python 3.",
        "buggy_code": """\
def check_guess(guess: str, secret: int) -> str:
    # BUG: guess is a string, secret is an int
    # == comparison always returns False; > raises TypeError in Python 3
    if guess == secret:
        return "win"
    if guess > secret:
        return "too_high"
    return "too_low"

result = check_guess("50", 42)   # raises TypeError
print(result)
""",
        "expected_bug_type": "type_error",
        "expected_keywords": ["type", "string", "int", "conversion"],
    },
    {
        "id": "scenario-004",
        "name": "Score Not Reset on New Game",
        "description": "start_new_game() forgets to reset the score.",
        "buggy_code": """\
import streamlit as st
import random

def start_new_game():
    st.session_state.secret = random.randint(1, 100)
    st.session_state.attempts = 0
    st.session_state.status = "playing"
    # BUG: score is never reset — it carries over from previous games
    # Missing: st.session_state.score = 0

if "secret" not in st.session_state:
    start_new_game()
    st.session_state.score = 0   # only set once, never reset

if st.button("New Game"):
    start_new_game()             # score persists here
""",
        "expected_bug_type": "state_management",
        "expected_keywords": ["score", "reset", "new game", "persist"],
    },
    {
        "id": "scenario-005",
        "name": "Game Accepts Guesses After Win",
        "description": "No status guard — player can keep guessing after winning.",
        "buggy_code": """\
import streamlit as st

# BUG: the submit handler never checks if the game is already over
# A player who has already won can keep clicking Submit
if st.button("Submit Guess"):
    guess = int(st.text_input("Enter guess"))
    if guess == st.session_state.secret:
        st.session_state.status = "won"
        st.success("You won!")
    elif st.session_state.attempts >= 10:
        st.session_state.status = "lost"
        st.error("Game over!")
    # Missing early exit:
    # if st.session_state.status != "playing":
    #     st.warning("Game is over. Start a new game.")
    #     st.stop()
""",
        "expected_bug_type": "control_flow",
        "expected_keywords": ["status", "guard", "stop", "game over"],
    },
]
