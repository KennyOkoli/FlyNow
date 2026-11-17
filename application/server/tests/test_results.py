import asyncio
from datetime import date, timedelta

from fastapi.testclient import TestClient

from server.results import ResultStore
from server.routers.flights import is_bookable
from server.schemas import SearchRequest


def _body(roundtrip_body: dict, days: int) -> dict:
    # A date no other test uses, so the first search here is never already stored.
    depart = date.today() + timedelta(days=days)
    return {**roundtrip_body, "departDate": depart.isoformat(), "returnDate": (depart + timedelta(days=7)).isoformat()}


def test_identical_search_is_served_from_the_database(client: TestClient, roundtrip_body: dict, monkeypatch) -> None:
    body = _body(roundtrip_body, 61)
    first = client.post("/api/flights/search", json=body).json()
    assert first["meta"]["cached"] is False

    provider = client.app.state.provider
    calls = []
    original = provider.search

    async def counting_search(query):
        calls.append(query)
        return await original(query)

    monkeypatch.setattr(provider, "search", counting_search)
    second = client.post("/api/flights/search", json=body).json()
    assert calls == []
    assert second["meta"]["cached"] is True
    assert second["searchId"] == first["searchId"]
    assert second["itineraries"] == first["itineraries"]

    other = client.post("/api/flights/search", json={**body, "cabin": "business"}).json()
    assert len(calls) == 1 and other["searchId"] != first["searchId"]


def test_detail_survives_a_restart(client: TestClient, roundtrip_body: dict) -> None:
    body = client.post("/api/flights/search", json=_body(roundtrip_body, 62)).json()
    itinerary_id = body["itineraries"][0]["id"]
    # A second backend task (or a restarted one) has its own ResultStore but the same database.
    app = client.app
    original = app.state.results
    app.state.results = ResultStore(app.state.db, timedelta(minutes=30))
    try:
        detail = client.get(f"/api/flights/{body['searchId']}/itineraries/{itinerary_id}")
    finally:
        app.state.results = original
    assert detail.status_code == 200
    assert detail.json()["id"] == itinerary_id


def test_expired_results_are_410(client: TestClient, roundtrip_body: dict) -> None:
    app = client.app
    original = app.state.results
    app.state.results = ResultStore(app.state.db, timedelta(minutes=-1))
    try:
        body = client.post("/api/flights/search", json=_body(roundtrip_body, 63)).json()
        detail = client.get(f"/api/flights/{body['searchId']}/itineraries/{body['itineraries'][0]['id']}")
        again = client.post("/api/flights/search", json=_body(roundtrip_body, 63)).json()
    finally:
        app.state.results = original
    assert detail.status_code == 410
    assert again["meta"]["cached"] is False and again["searchId"] != body["searchId"]


def test_offers_past_their_last_ticket_date_are_dropped(client: TestClient, roundtrip_body: dict) -> None:
    provider = client.app.state.provider
    result = asyncio.run(provider.search(SearchRequest.model_validate(_body(roundtrip_body, 64))))
    itinerary = result.itineraries[0]
    detail = result.details[itinerary.id]
    today = date.today()
    assert is_bookable(itinerary, detail.model_copy(update={"last_ticket_date": today}), today)
    assert not is_bookable(itinerary, detail.model_copy(update={"last_ticket_date": today - timedelta(days=1)}), today)
    assert not is_bookable(itinerary, detail, itinerary.legs[0].depart_at.date() + timedelta(days=1))
