"""
RAG retriever — bug pattern knowledge base with TF-IDF + cosine similarity.

No external model downloads required. Uses scikit-learn's TfidfVectorizer
to build a sparse index over the bug pattern corpus at startup.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_PATTERNS_PATH = Path(__file__).parent / "bug_patterns.json"


class BugRetriever:
    """
    Retrieves the most relevant bug patterns for a given query.

    Usage:
        retriever = BugRetriever()
        results = retriever.retrieve("backwards hint logic", top_k=3)
    """

    def __init__(self) -> None:
        self.patterns = self._load_patterns()
        self._vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            min_df=1,
        )
        self._index = self._build_index()

    # ── Private helpers ──────────────────────────────────────────────────────

    def _load_patterns(self) -> list[dict]:
        with open(_PATTERNS_PATH, encoding="utf-8") as f:
            return json.load(f)

    def _pattern_to_doc(self, p: dict) -> str:
        """Concatenate all searchable fields into a single string."""
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
        Return the top_k most relevant bug patterns for *query*.

        Each result is a copy of the pattern dict with an added
        'relevance_score' key (0.0 – 1.0).
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
        """Return a sorted list of unique bug categories."""
        return sorted({p["category"] for p in self.patterns})

    def get_by_category(self, category: str) -> list[dict]:
        """Return all patterns matching a given category."""
        return [p for p in self.patterns if p["category"] == category]
