"""
Scoring orchestrator: BM25, LLM, or a BM25+LLM blend.

Modes:
- bm25:   BM25 only.
- llm:    LLM only, BM25 fallback if the LLM call fails or the key is missing.
- hybrid: BM25 always runs. If an OpenAI key is configured, the LLM also runs and the two score sets are blended via
         `hybrid_alpha`: final = hybrid_alpha * bm25_score + (1 - hybrid_alpha) * llm_score
          BM25 fallback if the LLM call fails.

Caching:
- Successful responses are cached by sha256(mode + title + abstract).
- Fallback BM25 results (when the requested mode was llm/hybrid) are not cached
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


def _blend(
    bm25_results: list[dict],
    llm_results: list[dict],
    alpha: float,
) -> list[dict]:
    """
    Combine BM25 and LLM scores using equation final = alpha * bm25 + (1 - alpha) * llm.
    Results are returned sorted descending by the blended score.
    """
    bm25_map = {item["journal_id"]: item["score"] for item in bm25_results}
    blended = [
        {
            "journal_id": item["journal_id"],
            "score": round(
                alpha * bm25_map.get(item["journal_id"], 0.0)
                + (1 - alpha) * item["score"],
                4,
            ),
            "reasoning": item["reasoning"],
        }
        for item in llm_results
    ]
    blended.sort(key=lambda x: x["score"], reverse=True)
    return blended


async def _score(title: str, abstract: str) -> tuple[list[dict], str, str | None]:
    """Run the scoring pipeline and return (scored_results, actual_mode, model_used)."""
    mode = settings.scoring_mode

    if mode == "bm25":
        return score_bm25(title, abstract), "bm25", None

    if not _llm_available():
        logger.info(
            "OPENAI_API_KEY not set; using BM25 scoring. "
            "Set the key to enable LLM reranking."
        )
        return score_bm25(title, abstract), "bm25", None

    if mode == "llm":
        try:
            llm_scored = await score_llm(title, abstract)
            return llm_scored, "llm", settings.openai_model
        except RuntimeError as exc:
            logger.warning("LLM scoring failed, falling back to BM25: %s", exc)
            return score_bm25(title, abstract), "bm25", None

    bm25_scored = score_bm25(title, abstract)
    try:
        llm_scored = await score_llm(title, abstract)
    except RuntimeError as exc:
        logger.warning("LLM scoring failed, falling back to BM25-only: %s", exc)
        return bm25_scored, "bm25", None

    blended = _blend(bm25_scored, llm_scored, settings.hybrid_alpha)
    logger.info(
        "Hybrid blend complete (alpha=%.2f); top: %s (%.3f)",
        settings.hybrid_alpha,
        blended[0]["journal_id"],
        blended[0]["score"],
    )
    return blended, "hybrid", settings.openai_model


async def rank_journals(title: str, abstract: str) -> FindJournalResponse:
    """Main entry point for journal ranking."""
    mode = settings.scoring_mode
    cache_key = _cache_key(title, abstract, mode)

    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    scored, actual_mode, model_used = await _score(title, abstract)

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
