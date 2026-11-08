import logging
import secrets
from datetime import UTC, datetime

from fastapi import APIRouter, Request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from server.cache import SearchCache
from server.data import airlines_map, airports_map
from server.db import SearchRecord
from server.errors import NotFoundError, SearchExpiredError
from server.providers.base import FlightProvider
from server.schemas import ItineraryDetail, SearchMeta, SearchRequest, SearchResponse

logger = logging.getLogger("server")

router = APIRouter(prefix="/flights", tags=["flights"])

BASE_NOTES = ["Fares shown are indicative and not guaranteed until ticketed."]
MOCK_NOTES = ["Generated sample data, not live fares."]


@router.post("/search", response_model=SearchResponse)
async def search_flights(query: SearchRequest, request: Request) -> SearchResponse:
    provider: FlightProvider = request.app.state.provider
    cache: SearchCache = request.app.state.cache
    result = await provider.search(query)
    currency = result.itineraries[0].price.currency if result.itineraries else query.currency
    response = SearchResponse(
        search_id=f"srch_{secrets.token_hex(8)}",
        query=query,
        currency=currency,
        itineraries=result.itineraries,
        airlines=airlines_map(result.airline_codes),
        airports=airports_map(result.airport_codes),
        meta=SearchMeta(count=len(result.itineraries), provider=provider.name, fetched_at=datetime.now(UTC)),
    )
    cache.put(response, result.details)
    await save_search(request.app.state.db, response)
    return response


async def save_search(sessions: async_sessionmaker[AsyncSession], response: SearchResponse) -> None:
    query = response.query
    record = SearchRecord(
        search_id=response.search_id,
        origin=query.origin,
        destination=query.destination,
        trip_type=query.trip_type,
        depart_date=query.depart_date,
        return_date=query.return_date,
        adults=query.passengers.adults,
        children=query.passengers.children,
        infants=query.passengers.infants,
        cabin=query.cabin,
        currency=query.currency,
        result_count=response.meta.count,
        provider=response.meta.provider,
    )
    # A failed write must not cost the user their search results.
    try:
        async with sessions() as session:
            session.add(record)
            await session.commit()
    except SQLAlchemyError:
        logger.exception("Could not save search %s", response.search_id)


@router.get("/{search_id}/itineraries/{itinerary_id}", response_model=ItineraryDetail)
async def get_itinerary(search_id: str, itinerary_id: str, request: Request) -> ItineraryDetail:
    cache: SearchCache = request.app.state.cache
    entry = cache.get(search_id)
    if entry is None:
        raise SearchExpiredError(f"Search {search_id} is unknown or has expired; run the search again")
    itinerary = entry.itineraries.get(itinerary_id)
    if itinerary is None:
        raise NotFoundError(f"Itinerary {itinerary_id} is not part of search {search_id}")
    detail = entry.details[itinerary_id]
    airline_codes = {itinerary.validating_carrier} | {
        c for leg in itinerary.legs for seg in leg.segments for c in (seg.marketing_carrier, seg.operating_carrier)
    }
    airport_codes = {a for leg in itinerary.legs for seg in leg.segments for a in (seg.from_, seg.to)}
    notes = BASE_NOTES + (MOCK_NOTES if entry.response.meta.provider == "mock" else [])
    return ItineraryDetail(
        **itinerary.model_dump(by_alias=False),
        **detail.model_dump(by_alias=False),
        search_id=search_id,
        query=entry.response.query,
        airlines={code: entry.response.airlines.get(code, code) for code in sorted(airline_codes)},
        airports={code: entry.response.airports[code] for code in sorted(airport_codes) if code in entry.response.airports},
        notes=notes,
    )
