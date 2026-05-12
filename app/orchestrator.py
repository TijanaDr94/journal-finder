"""
Hybrid scorer: BM25 for the initial ranking, then optional LLM reranking.

Flow:
- Build a cache key from (mode, title, abstract) and return cached results when available.
- Use BM25 to generate a fast baseline ranking.
- If OpenAI is configured and LLM scoring is enabled, rerank the journals with the LLM.
- If the LLM call fails, fall back to the BM25 results and log the error.
- Cache successful responses, but never cache BM25 fallback results caused by a temporary LLM outage.
"""

import hashlib
import logging
from collections import OrderedDict

from app.config import settings
from app.journals import JOURNAL_MAP
from app.schemas import FindJournalResponse, JournalScore
from app.scorer_bm25 import score_bm25
from app.scorer_llm import score_llm

logger = logging.getLogger(__name__)


_response_cache: "OrderedDict[str, FindJournalResponse]" = OrderedDict()


def _cache_key(title: str, abstract: str, mode: str) -> str:
    """Create deterministic cache key for a request."""
    hasher = hashlib.sha256()
    hasher.update(mode.encode())
    hasher.update(b"\0")
    hasher.update(title.encode())
    hasher.update(b"\0")
    hasher.update(abstract.encode())
    return hasher.hexdigest()


def _cache_get(key: str) -> FindJournalResponse | None:
    """Retrieve cached response and refresh LRU order."""
    response = _response_cache.get(key)
    if response is not None:
        _response_cache.move_to_end(key)
    return response


def _cache_set(key: str, response: FindJournalResponse) -> None:
    """Store response in cache and evict the oldest entries if needed."""
    _response_cache[key] = response
    _response_cache.move_to_end(key)
    while len(_response_cache) > settings.cache_max_size:
        _response_cache.popitem(last=False)


def cache_clear() -> None:
    """Drop all cached responses (used by tests)."""
    _response_cache.clear()


def _llm_available() -> bool:
    """Check whether OpenAI API key is configured."""
    return bool(settings.openai_api_key)


async def rank_journals(title: str, abstract: str) -> FindJournalResponse:
    """Main entry point for journal ranking."""
    mode = settings.scoring_mode
    cache_key = _cache_key(title, abstract, mode)

    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    use_llm = _llm_available() and mode in ("hybrid", "llm")

    scored: list[dict] = []
    actual_mode: str
    model_used: str | None = None

    if use_llm:
        try:
            scored = await score_llm(title, abstract)
            actual_mode = "llm" if mode == "llm" else "hybrid"
            model_used = settings.openai_model
            logger.info("Scored via LLM (%s)", settings.openai_model)
        except RuntimeError as exc:
            logger.warning("LLM scoring failed, falling back to BM25: %s", exc)
            scored = score_bm25(title, abstract)
            actual_mode = "bm25"
    else:
        if mode in ("hybrid", "llm") and not _llm_available():
            logger.info(
                "OPENAI_API_KEY not set; using BM25 scoring. "
                "Set the key to enable LLM reranking."
            )
        scored = score_bm25(title, abstract)
        actual_mode = "bm25"

    ranked: list[JournalScore] = []
    for rank, item in enumerate(scored, start=1):
        journal = JOURNAL_MAP.get(item["journal_id"])
        if journal is None:
            logger.warning("Skipping unknown journal_id from scorer: %s", item["journal_id"])
            continue
        ranked.append(
            JournalScore(
                journal_id=journal.id,
                journal_name=journal.name,
                issn=journal.issn,
                url=journal.url,
                score=round(item["score"], 4),
                rank=rank,
                reasoning=item.get("reasoning"),
            )
        )

    response = FindJournalResponse(
        ranked_journals=ranked,
        scoring_method=actual_mode,
        model_used=model_used,
    )

    if mode == "bm25" or actual_mode in ("llm", "hybrid"):
        _cache_set(cache_key, response)

    return response
