from dataclasses import dataclass, field
from typing import Literal, Protocol

from server.schemas import Itinerary, ItineraryDetailFields, SearchRequest

ProviderName = Literal["sabre", "mock"]


@dataclass
class SearchResult:
    itineraries: list[Itinerary]
    details: dict[str, ItineraryDetailFields]
    airline_codes: set[str] = field(default_factory=set)
    airport_codes: set[str] = field(default_factory=set)


class FlightProvider(Protocol):
    name: ProviderName

    async def search(self, query: SearchRequest) -> SearchResult: ...
