"""FastAPI application entrypoint for the Journal Finder service."""

import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _parse_cors_origins(raw: str) -> list[str]:
    """Parses comma-separated CORS origins from configuration."""
    return [origin.strip() for origin in raw.split(",") if origin.strip()] or ["*"]


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description=(
        "Given the title and abstract of a scientific manuscript, "
        "returns a ranked list of MDPI journals with relevance scores."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_cors_origins(settings.cors_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id_and_timing(request: Request, call_next):
    """Adds request ID and processing time headers to each response."""
    request_id = request.headers.get("Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time

    response.headers["Request-ID"] = request_id
    response.headers["Process-Time"] = f"{process_time:.4f}"
    return response


@app.get("/health", tags=["Meta"])
async def health():
    """Liveness probe."""
    return {"status": "ok", "version": settings.app_version}

