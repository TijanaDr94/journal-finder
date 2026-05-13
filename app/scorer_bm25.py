"""
The scorer (BM25 + keyword overlap) compares the paper abstract against the journal scope descriptions.

How it works:
- BM25 provides the main relevance score based on term frequency.
- A keyword overlap check boosts journals whose core terms explicitly appear in the abstract.
- The final score combines both signals and normalizes them to [0, 1].

This approach is fast and simple to explain and good enough for a small fixed set of journals.

Note:
It relies on wording, so it can miss synonyms words. Also BM25 may slightly favor longer scope descriptions,
which the keyword overlap step helps balance.
"""

import re

import numpy as np
from rank_bm25 import BM25Okapi

from app.journals import JOURNALS, Journal

_PUNCT_RE = re.compile(r"[^\w\s]")

# Common English stopwords and generic academic terms that add noise to BM25
_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "not", "no", "nor",
    "so", "yet", "both", "either", "neither", "as", "if", "then", "than",
    "that", "this", "these", "those", "it", "its", "we", "our", "they",
    "their", "which", "who", "whom", "what", "when", "where", "how", "why",
    "all", "each", "every", "few", "more", "most", "other", "some", "such",
    "into", "through", "about", "between", "after", "before", "also",
    # generic academic terms
    "study", "studies", "result", "results", "method", "methods",
    "approach", "approaches", "analysis", "analyses",
    "model", "models", "paper", "papers", "system", "systems",
    "data", "research", "novel", "based", "using", "proposed",
    "present", "presents", "presented", "show", "shows", "shown",
    "use", "used", "uses", "work", "works",
}

_BM25_WEIGHT = 0.6
_KEYWORD_WEIGHT = 0.4


def _tokenise(text: str) -> list[str]:
    """Lowercase, strip punctuation, remove stopwords, return token list."""
    text = text.lower()
    text = _PUNCT_RE.sub(" ", text)
    tokens = text.split()
    return [token for token in tokens if token not in _STOPWORDS and len(token) > 1]


def _build_corpus() -> tuple[list[list[str]], BM25Okapi]:
    """Build tokenised corpus and BM25 index from scope + keywords."""
    corpus = [
        _tokenise(journal.scope + " " + " ".join(journal.keywords))
        for journal in JOURNALS
    ]
    bm25 = BM25Okapi(corpus)
    return corpus, bm25


def _build_keyword_patterns() -> dict[str, list[re.Pattern[str]]]:
    """Precompile word-boundary regex patterns for every journal's keywords."""
    patterns: dict[str, list[re.Pattern[str]]] = {}
    for journal in JOURNALS:
        patterns[journal.id] = [
            re.compile(r"\b" + re.escape(kw.lower()) + r"\b") for kw in journal.keywords
        ]
    return patterns

_corpus, _bm25 = _build_corpus()
_KEYWORD_PATTERNS = _build_keyword_patterns()


def _keyword_score(text_lower: str, journal: Journal) -> float:
    """Fraction of journal's keyword list found in the text."""
    patterns = _KEYWORD_PATTERNS[journal.id]
    if not patterns:
        return 0.0
    hits = sum(1 for pattern in patterns if pattern.search(text_lower))
    return hits / len(patterns)


def _normalise(scores: np.ndarray) -> np.ndarray:
    """Min-max normalise to [0, 1]"""

    min_score = scores.min()
    max_score = scores.max()

    if max_score - min_score < 1e-9:
        return np.ones_like(scores) / len(scores)
    return (scores - min_score) / (max_score - min_score)


def score_bm25(title: str, abstract: str) -> list[dict]:
    """Return a list of dicts (journal_id, raw_score) sorted descending."""
    query_text = f"{title} {abstract}"
    query_tokens = _tokenise(query_text)
    text_lower = query_text.lower()

    bm25_scores = np.array(_bm25.get_scores(query_tokens), dtype=float)
    keyword_match_ratio = np.array(
        [_keyword_score(text_lower, journal) for journal in JOURNALS], dtype=float
    )

    bm25_scaled = _normalise(bm25_scores)
    keyword_scaled = _normalise(keyword_match_ratio)

    weighted_score = _BM25_WEIGHT * bm25_scaled + _KEYWORD_WEIGHT * keyword_scaled
    final_score = _normalise(weighted_score)

    results = [
        {"journal_id": journal.id, "score": float(final_score[index])}
        for index, journal in enumerate(JOURNALS)
    ]
    results.sort(key=lambda x: x["score"], reverse=True)
    return results
