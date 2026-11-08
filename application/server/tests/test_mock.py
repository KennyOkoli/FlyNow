import json
from datetime import date, timedelta

import pytest

from server.providers.mock import MockProvider
from server.schemas import Itinerary, Passengers, SearchRequest


def _query(**overrides: object) -> SearchRequest:
    base: dict = {
        "trip_type": "oneway",
        "origin": "LOS",
        "destination": "LHR",
        "depart_date": date.today() + timedelta(days=21),
        "passengers": Passengers(adults=2, children=1, infants=1),
        "cabin": "economy",
        "currency": "USD",
    }
    base.update(overrides)
    return SearchRequest(**base)


async def test_oneway_results_are_valid_and_deterministic() -> None:
    provider = MockProvider()
    first = await provider.search(_query())
    second = await provider.search(_query())
    assert 15 <= len(first.itineraries) <= 25
    assert [i.model_dump() for i in first.itineraries] == [i.model_dump() for i in second.itineraries]
    for itinerary in first.itineraries:
        Itinerary.model_validate(json.loads(itinerary.model_dump_json()))
        assert len(itinerary.legs) == 1
        assert itinerary.legs[0].from_ == "LOS" and itinerary.legs[0].to == "LHR"
        assert itinerary.price.total == pytest.approx(itinerary.price.base + itinerary.price.taxes, abs=0.05)
        for segment in itinerary.legs[0].segments[1:]:
            assert segment.layover_minutes is not None and 60 <= segment.layover_minutes <= 360
    assert {len(i.legs[0].segments) for i in first.itineraries} >= {1, 2}
    assert [i.price.total for i in first.itineraries] == sorted(i.price.total for i in first.itineraries)
    assert first.details.keys() == {i.id for i in first.itineraries}


async def test_roundtrip_has_two_mirrored_legs() -> None:
    result = await MockProvider().search(
        _query(trip_type="roundtrip", return_date=date.today() + timedelta(days=28), cabin="business")
    )
    for itinerary in result.itineraries:
        assert len(itinerary.legs) == 2
        outbound, inbound = itinerary.legs
        assert (outbound.from_, outbound.to) == ("LOS", "LHR")
        assert (inbound.from_, inbound.to) == ("LHR", "LOS")
        assert inbound.depart_at > outbound.arrive_at
        assert itinerary.cabin == "business"
        assert [s.to for s in outbound.segments][:-1] == [s.from_ for s in inbound.segments][1:][::-1]
    assert result.airline_codes and result.airport_codes >= {"LOS", "LHR"}


async def test_currency_and_fare_breakdown() -> None:
    usd = await MockProvider().search(_query())
    ngn = await MockProvider().search(_query(currency="NGN"))
    assert ngn.itineraries[0].price.currency == "NGN"
    assert ngn.itineraries[0].price.total == pytest.approx(usd.itineraries[0].price.total * 1550, rel=0.01)
    breakdown = usd.details["it_1"].fare_breakdown
    assert [item.passenger_type for item in breakdown] == ["adult", "child", "infant"]
    assert [item.count for item in breakdown] == [2, 1, 1]
    taxes = usd.details["it_1"].taxes
    assert sum(t.amount for t in taxes) == pytest.approx(breakdown[0].taxes, abs=0.05)


async def test_domestic_nigeria_is_nonstop_on_local_carriers() -> None:
    result = await MockProvider().search(_query(destination="ABV", passengers=Passengers(adults=1)))
    assert all(it.legs[0].stops == 0 for it in result.itineraries)
    assert result.airline_codes <= {"W3", "P4", "Q9", "9J", "VL"}
