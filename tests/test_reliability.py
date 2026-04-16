"""
Reliability tests for the debug agent and RAG retriever.

- TestRetriever: local, no API key required.
- TestAgentReliability: end-to-end, requires ANTHROPIC_API_KEY.
  Skipped automatically in CI if the key is absent.
"""
import os

import pytest

from src.rag.retriever import BugRetriever


# ── RAG Retriever tests (no API needed) ───────────────────────────────────────


class TestRetriever:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.retriever = BugRetriever()

    def test_patterns_loaded(self):
        assert len(self.retriever.patterns) >= 10

    def test_returns_results_for_known_query(self):
        results = self.retriever.retrieve("backwards hint logic direction", top_k=3)
        assert len(results) > 0

    def test_backwards_hint_is_top_result(self):
        results = self.retriever.retrieve("hint messages reversed go higher go lower", top_k=1)
        assert results[0]["id"] == "bp-001"

    def test_state_management_category_present(self):
        results = self.retriever.retrieve("session_state not initialized rerun reset", top_k=3)
        categories = [r["category"] for r in results]
        assert "state_management" in categories

    def test_type_error_pattern_retrievable(self):
        results = self.retriever.retrieve("int string comparison type mismatch TypeError", top_k=3)
        ids = [r["id"] for r in results]
        assert "bp-003" in ids

    def test_irrelevant_query_returns_low_scores(self):
        results = self.retriever.retrieve("quantum entanglement nuclear physics", top_k=3)
        for r in results:
            assert r["relevance_score"] < 0.3, (
                f"Expected low score for unrelated query, got {r['relevance_score']} for {r['id']}"
            )

    def test_results_sorted_by_score_descending(self):
        results = self.retriever.retrieve("streamlit state bug reset", top_k=5)
        scores = [r["relevance_score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_get_all_categories(self):
        cats = self.retriever.get_all_categories()
        assert "logic_error" in cats
        assert "state_management" in cats
        assert "type_error" in cats

    def test_get_by_category_filters_correctly(self):
        results = self.retriever.get_by_category("type_error")
        assert all(r["category"] == "type_error" for r in results)


# ── Agent reliability tests (require API key) ─────────────────────────────────


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping live agent tests",
)
class TestAgentReliability:
    """
    End-to-end tests that call the Claude API.
    Marked @pytest.mark.slow — exclude with: pytest -m "not slow"
    """

    @pytest.mark.slow
    def test_agent_detects_backwards_hint(self):
        from src.game.scenarios import SCENARIOS
        from src.agent.debug_agent import analyze_code

        scenario = next(s for s in SCENARIOS if s["id"] == "scenario-001")
        result = analyze_code(scenario["buggy_code"])
        report = result["report"].lower()
        assert any(kw in report for kw in scenario["expected_keywords"]), (
            f"Expected one of {scenario['expected_keywords']} in report.\nReport: {report[:500]}"
        )

    @pytest.mark.slow
    def test_agent_uses_search_tool(self):
        from src.game.scenarios import SCENARIOS
        from src.agent.debug_agent import analyze_code

        scenario = SCENARIOS[0]
        result = analyze_code(scenario["buggy_code"])
        assert result["tool_calls"], "Agent should have called search_bug_patterns at least once"

    @pytest.mark.slow
    def test_agent_returns_non_empty_report(self):
        from src.game.scenarios import SCENARIOS
        from src.agent.debug_agent import analyze_code

        scenario = next(s for s in SCENARIOS if s["id"] == "scenario-002")
        result = analyze_code(scenario["buggy_code"])
        assert len(result["report"]) > 100, "Report should contain meaningful content"

    @pytest.mark.slow
    def test_agent_identifies_type_error(self):
        from src.game.scenarios import SCENARIOS
        from src.agent.debug_agent import analyze_code

        scenario = next(s for s in SCENARIOS if s["id"] == "scenario-003")
        result = analyze_code(scenario["buggy_code"])
        report = result["report"].lower()
        assert any(kw in report for kw in scenario["expected_keywords"]), (
            f"Expected type-error keywords. Report: {report[:500]}"
        )
