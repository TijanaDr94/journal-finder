"""Pydantic request and response schemas for the Journal Finder API."""

from pydantic import BaseModel, ConfigDict, Field


class FindJournalRequest(BaseModel):
    """Request body for the /find-journal endpoint."""
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Manuscript title.",
    )
    abstract: str = Field(
        ...,
        min_length=50,
        max_length=20_000,
        description="Manuscript abstract.",
        examples=[
            "We present a novel transformer-based architecture for text classification... "
        ],
    )


class JournalScore(BaseModel):
    """Relevance score and metadata for a single journal."""
    journal_id: str = Field(description="Internal journal identifier.")
    journal_name: str = Field(description="Name of the journal.")
    issn: str = Field(description="ISSN of the journal.")
    url: str = Field(description="URL of the journal's homepage.")
    score: float = Field(
        description="Relevance score in [0, 1]. Higher means better fit.",
        ge=0.0,
        le=1.0,
    )
    rank: int = Field(description="Journal rank (1 = best fit).")
    reasoning: str | None = Field(
        default=None,
        description="Brief explanation for the ranking. Present only for LLM scoring.",
    )


class FindJournalResponse(BaseModel):
    """Response returned by the /find-journal endpoint."""
    ranked_journals: list[JournalScore] = Field(
        description="Journals ranked from most to least suitable."
    )
    scoring_method: str = Field(
        description="Method used for ranking: 'bm25', 'llm', or 'hybrid'."
    )
    model_used: str | None = Field(
        default=None,
        description="LLM model used for scoring",
    )
