""" Application configuration """

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """ Settings for the Journal Finder service. """
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    scoring_mode: Literal["hybrid", "bm25", "llm"] = "hybrid"
    llm_temperature: float = 0.0
    llm_max_tokens: int = 800
    # used in hybrid mode: final_score = hybrid_alpha * bm25_score + (1 - hybrid_alpha) * llm_score
    # 0.0 = pure LLM, 1.0 = pure BM25, 0.3 = LLM-dominant
    hybrid_alpha: float = 0.3
    cache_max_size: int = 256
    cors_origins: str = "*"

    app_title: str = "MDPI Journal Finder"
    app_version: str = "0.1.0"


settings = Settings()
