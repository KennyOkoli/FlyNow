from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from server.schemas import Itinerary, ItineraryDetailFields, SearchResponse


@dataclass
class CachedSearch:
    expires_at: datetime
    response: SearchResponse
    itineraries: dict[str, Itinerary]
    details: dict[str, ItineraryDetailFields]


class SearchCache:
    def __init__(self, ttl: timedelta) -> None:
        self._ttl = ttl
        self._entries: dict[str, CachedSearch] = {}

    def put(self, response: SearchResponse, details: dict[str, ItineraryDetailFields]) -> None:
        self._prune()
        self._entries[response.search_id] = CachedSearch(
            expires_at=datetime.now(UTC) + self._ttl,
            response=response,
            itineraries={it.id: it for it in response.itineraries},
            details=details,
        )

    def get(self, search_id: str) -> CachedSearch | None:
        entry = self._entries.get(search_id)
        if entry is None:
            return None
        if entry.expires_at <= datetime.now(UTC):
            del self._entries[search_id]
            return None
        return entry

    def _prune(self) -> None:
        now = datetime.now(UTC)
        for key in [k for k, v in self._entries.items() if v.expires_at <= now]:
            del self._entries[key]

    def __len__(self) -> int:
        return len(self._entries)
