"""
LLM-based journal scorer using OpenAI structured outputs.

The model receives the manuscript title, abstract, and short journal scope
descriptions, then ranks the journals by relevance and explains each choice.

Structured JSON output keeps responses predictable and avoids manual parsing
issues. AsyncOpenAI is used so waiting on OpenAI never blocks the FastAPI
server.

The LLM scorer understands semantics, synonyms, and domain context far better
than BM25. It requires an OpenAI API key and is slower than BM25.
"""

import json
import logging
import textwrap
from functools import cache
from typing import Any, cast

from openai import AsyncOpenAI, OpenAIError
from openai.types.chat import ChatCompletionMessageParam
from openai.types.shared_params import ResponseFormatJSONSchema

from app.config import settings
from app.journals import JOURNALS

logger = logging.getLogger(__name__)


_SYSTEM_PROMPT = """\
You are an expert scientific editor at MDPI specializing in manuscript evaluation and 
journal assignment. Given a manuscript abstract, your task is to rank candidate journals 
based on how well their scope matches the content of the manuscript.

Rules:
- Score each journal 0-100 (higher = better fit).
- Scores must be distinct (no ties).
- Scores must span at least 20 points between the highest and lowest.
- Base scores solely on topical relevance to each journal's scope.
- Provide a 1-2 sentence justification per journal.
- Return exactly one entry per provided journal - no duplicates, no omissions.
"""


_JOURNAL_IDS: list[str] = [journal.id for journal in JOURNALS]
_EXPECTED_IDS: set[str] = set(_JOURNAL_IDS)


def _build_journal_block() -> str:
    """Build prompt block with journal scopes."""
    block = "Candidate journals and their scopes:\n\n"
    for journal in JOURNALS:
        condensed = textwrap.shorten(journal.scope, width=600, placeholder="…")
        block += (
            "--- JOURNAL ---\n"
            f"ID: {journal.id}\n"
            f"Name: {journal.name}\n"
            f"Scope: {condensed}\n"
            "--- END JOURNAL ---\n\n"
        )
    return block


_JOURNAL_BLOCK: str = _build_journal_block()


def _response_schema() -> dict[str, Any]:
    """JSON schema for OpenAI strict structured output."""
    return {
        "type": "object",
        "properties": {
            "rankings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "journal_id": {"type": "string", "enum": _JOURNAL_IDS},
                        "score": {"type": "integer", "minimum": 0, "maximum": 100},
                        "reasoning": {"type": "string"},
                    },
                    "required": ["journal_id", "score", "reasoning"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["rankings"],
        "additionalProperties": False,
    }


def _build_user_prompt(title: str, abstract: str) -> str:
    """Build the user prompt sent to the LLM."""
    header = f'Manuscript title: "{title}"\n\n'
    header += f"Abstract:\n{abstract}\n\n"
    return header + _JOURNAL_BLOCK + "Return the JSON now."


@cache
def _get_client() -> AsyncOpenAI:
    """Return a cached AsyncOpenAI client instance."""
    return AsyncOpenAI(api_key=settings.openai_api_key)


def reset_client() -> None:
    """Clear the cached OpenAI client. Useful for tests after env changes."""
    _get_client.cache_clear()


def _validate_rankings(rankings: list[dict]) -> None:
    """Ensure LLM returned exactly one entry per known journal_id."""
    returned_ids = [item["journal_id"] for item in rankings]
    if len(returned_ids) != len(_EXPECTED_IDS) or set(returned_ids) != _EXPECTED_IDS:
        raise RuntimeError(
            f"LLM returned invalid journal_ids: expected {sorted(_EXPECTED_IDS)}, "
            f"got {sorted(returned_ids)}"
        )


def _build_request_payload(title: str, abstract: str) -> tuple[
    list[ChatCompletionMessageParam], ResponseFormatJSONSchema
]:
    """Build the messages list and response format for the OpenAI call."""
    messages = cast(
        list[ChatCompletionMessageParam],
        [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(title, abstract)},
        ],
    )
    response_format = cast(
        ResponseFormatJSONSchema,
        {
            "type": "json_schema",
            "json_schema": {
                "name": "journal_rankings",
                "strict": True,
                "schema": _response_schema(),
            },
        },
    )
    return messages, response_format


async def _call_openai(
    messages: list[ChatCompletionMessageParam],
    response_format: ResponseFormatJSONSchema,
) -> list[dict]:
    """Call OpenAI and return the parsed rankings array."""
    try:
        response = await _get_client().chat.completions.create(
            model=settings.openai_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            messages=messages,
            response_format=response_format,
        )
    except OpenAIError as exc:
        raise RuntimeError(f"OpenAI API error: {exc}") from exc

    try:
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("OpenAI returned empty content")
        return json.loads(content)["rankings"]
    except (KeyError, IndexError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Failed to parse OpenAI response: {exc}") from exc


def _normalise_rankings(rankings: list[dict]) -> list[dict]:
    """Normalise raw 0–100 scores to [0, 1] and sort descending."""
    raw_scores = [item["score"] for item in rankings]
    score_min, score_max = min(raw_scores), max(raw_scores)
    span = score_max - score_min

    if span == 0:
        logger.warning(
            "LLM returned identical scores for all journals; "
            "normalisation collapsed to uniform values."
        )

    results = [
        {
            "journal_id": item["journal_id"],
            "score": round(
                (item["score"] - score_min) / span if span > 0 else 1.0 / len(rankings),
                4,
            ),
            "reasoning": item["reasoning"],
        }
        for item in rankings
    ]
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


async def score_llm(title: str, abstract: str) -> list[dict]:
    """
    Call OpenAI and return scored journals sorted descending by score.
    Raises RuntimeError on missing key, API failure, or when the LLM returns
    an invalid set of journal_ids.
    """
    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Set it to enable LLM scoring."
        )

    messages, response_format = _build_request_payload(title, abstract)
    rankings = await _call_openai(messages, response_format)

    if not rankings:
        raise RuntimeError("OpenAI returned an empty rankings array")

    _validate_rankings(rankings)
    normalised = _normalise_rankings(rankings)
    logger.info(
        "LLM ranked %d journals; top: %s (%.3f)",
        len(normalised),
        normalised[0]["journal_id"],
        normalised[0]["score"],
    )
    return normalised
