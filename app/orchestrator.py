import logging

from app.schemas import FindJournalResponse

logger = logging.getLogger(__name__)


async def rank_journals(title: str, abstract: str) -> FindJournalResponse:
    pass