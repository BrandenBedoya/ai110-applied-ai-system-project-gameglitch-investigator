"""
RAG retriever — multi-source bug pattern knowledge base with TF-IDF + cosine similarity.

RAG Enhancement (stretch feature):
  Two JSON sources are indexed together, giving the retriever broader coverage:
    - game_bugs       → bug_patterns.json    (15 Streamlit/game-specific patterns)
    - python_pitfalls → python_pitfalls.json (8 general Python anti-patterns)

  Each result includes a 'source' field so callers can see which KB it came from.
  No external model downloads required.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ── Data sources ──────────────────────────────────────────────────────────────

_PATTERN_SOURCES: dict[str, Path] = {
    "game_bugs": Path(__file__).parent / "bug_patterns.json",
    "python_pitfalls": Path(__file__).parent / "python_pitfalls.json",
}


class BugRetriever:
    """
    Retrieves the most relevant bug patterns across all configured sources.

    Usage:
        retriever = BugRetriever()
        results = retriever.retrieve("mutable default argument", top_k=3)
        # Each result includes a 'source' field: 'game_bugs' or 'python_pitfalls'
    """

    def __init__(self) -> None:
        self.patterns = self._load_all_patterns()
        self._vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            min_df=1,
        )
        self._index = self._build_index()

    # ── Private helpers ──────────────────────────────────────────────────────

    def _load_all_patterns(self) -> list[dict]:
        """Load and tag patterns from every configured source file."""
        all_patterns: list[dict] = []
        for source_name, path in _PATTERN_SOURCES.items():
            with open(path, encoding="utf-8") as f:
                patterns: list[dict] = json.load(f)
            for p in patterns:
                p["source"] = source_name  # tag so callers know the origin
            all_patterns.extend(patterns)
        return all_patterns

    def _pattern_to_doc(self, p: dict) -> str:
        """Concatenate all searchable fields into one string for TF-IDF."""
        tags = " ".join(p.get("tags", []))
        return (
            f"{p['title']} {p['description']} {p['symptoms']} "
            f"{p.get('code_smell', '')} {tags}"
        )

    def _build_index(self):
        docs = [self._pattern_to_doc(p) for p in self.patterns]
        return self._vectorizer.fit_transform(docs)

    # ── Public API ───────────────────────────────────────────────────────────

    def retrieve(self, query: str, top_k: int = 3) -> list[dict]:
        """
        Return the top_k most relevant patterns across all sources for *query*.

        Each result is a copy of the pattern dict with two added keys:
          - 'relevance_score' (float 0.0–1.0)
          - 'source' (str: 'game_bugs' | 'python_pitfalls')
        """
        query_vec = self._vectorizer.transform([query])
        scores: np.ndarray = cosine_similarity(query_vec, self._index).flatten()
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0.0:
                entry = dict(self.patterns[idx])
                entry["relevance_score"] = round(float(scores[idx]), 4)
                results.append(entry)
        return results

    def get_all_categories(self) -> list[str]:
        """Return sorted unique bug categories across all sources."""
        return sorted({p["category"] for p in self.patterns})

    def get_by_category(self, category: str) -> list[dict]:
        """Return all patterns matching a category across all sources."""
        return [p for p in self.patterns if p["category"] == category]

    def get_sources(self) -> list[str]:
        """Return the list of loaded source names."""
        return list(_PATTERN_SOURCES.keys())
