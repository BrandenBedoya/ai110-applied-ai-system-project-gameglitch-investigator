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

    # ── Core retrieval ────────────────────────────────────────────────────────

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

    # ── RAG Enhancement: multi-source tests ───────────────────────────────────

    def test_both_sources_loaded(self):
        """RAG Enhancement: retriever must load from both JSON sources."""
        sources = {p["source"] for p in self.retriever.patterns}
        assert "game_bugs" in sources, "game_bugs source missing"
        assert "python_pitfalls" in sources, "python_pitfalls source missing"

    def test_total_pattern_count_includes_both_sources(self):
        """RAG Enhancement: combined corpus should have 23 patterns (15 + 8)."""
        assert len(self.retriever.patterns) == 23

    def test_python_pitfall_retrievable(self):
        """
        RAG Enhancement — measurable improvement:
        Before: query 'mutable default argument list parameter' returned 0 results
                (no game-specific pattern matched it).
        After:  pp-001 from python_pitfalls source is returned in top results.
        """
        results = self.retriever.retrieve("mutable default argument list parameter", top_k=3)
        ids = [r["id"] for r in results]
        assert "pp-001" in ids, (
            "Expected pp-001 (Mutable Default Argument) from python_pitfalls source"
        )

    def test_python_pitfall_results_include_source_field(self):
        """RAG Enhancement: results must carry a 'source' field for attribution."""
        results = self.retriever.retrieve("mutable default argument", top_k=3)
        assert all("source" in r for r in results)

    def test_bare_except_retrievable_from_pitfalls(self):
        """RAG Enhancement: general Python pattern from second source is reachable."""
        results = self.retriever.retrieve("bare except clause swallow exception", top_k=3)
        ids = [r["id"] for r in results]
        assert "pp-003" in ids

    def test_cross_source_query_returns_mixed_results(self):
        """RAG Enhancement: a broad query can return patterns from both sources."""
        results = self.retriever.retrieve("logic error comparison wrong", top_k=5)
        sources = {r["source"] for r in results}
        assert len(sources) > 1, "Expected results from more than one source for a broad query"


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
