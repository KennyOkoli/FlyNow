import hashlib
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from server.db import SearchResultRecord
from server.schemas import Itinerary, ItineraryDetailFields, SearchRequest, SearchResponse

logger = logging.getLogger("server")

# Rows this far past their expiry are deleted the next time a search is saved.
CLEANUP_AFTER = timedelta(days=1)


@dataclass
class StoredSearch:
    response: SearchResponse
    itineraries: dict[str, Itinerary]
    details: dict[str, ItineraryDetailFields]


def query_key(provider: str, query: SearchRequest) -> str:
    return hashlib.sha256(f"{provider}|{query.model_dump_json()}".encode()).hexdigest()


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _load(record: SearchResultRecord) -> StoredSearch:
    response = SearchResponse.model_validate(record.payload["response"])
    details = {key: ItineraryDetailFields.model_validate(value) for key, value in record.payload["details"].items()}
    return StoredSearch(response=response, itineraries={it.id: it for it in response.itineraries}, details=details)


class ResultStore:
    """Search results shared by every backend task. Database errors never fail a search: it just isn't reused."""

    def __init__(self, sessions: async_sessionmaker[AsyncSession], ttl: timedelta) -> None:
        self._sessions = sessions
        self._ttl = ttl

    async def find_fresh(self, key: str) -> StoredSearch | None:
        statement = (
            select(SearchResultRecord)
            .where(SearchResultRecord.query_key == key, SearchResultRecord.expires_at > _now())
            .order_by(SearchResultRecord.created_at.desc())
            .limit(1)
        )
        try:
            async with self._sessions() as session:
                record = (await session.execute(statement)).scalar_one_or_none()
        except SQLAlchemyError:
            logger.exception("Could not look up stored results")
            return None
        return _load(record) if record else None

    async def get(self, search_id: str) -> StoredSearch | None:
        try:
            async with self._sessions() as session:
                record = await session.get(SearchResultRecord, search_id)
        except SQLAlchemyError:
            logger.exception("Could not load stored results for %s", search_id)
            return None
        if record is None or record.expires_at <= _now():
            return None
        return _load(record)

    async def put(self, key: str, response: SearchResponse, details: dict[str, ItineraryDetailFields]) -> None:
        now = _now()
        record = SearchResultRecord(
            search_id=response.search_id,
            query_key=key,
            payload={
                "response": response.model_dump(mode="json"),
                "details": {k: v.model_dump(mode="json") for k, v in details.items()},
            },
            created_at=now,
            expires_at=now + self._ttl,
        )
        try:
            async with self._sessions() as session:
                session.add(record)
                await session.execute(delete(SearchResultRecord).where(SearchResultRecord.expires_at < now - CLEANUP_AFTER))
                await session.commit()
        except SQLAlchemyError:
            logger.exception("Could not store results for %s", response.search_id)
