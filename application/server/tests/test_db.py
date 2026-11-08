import asyncio

from fastapi.testclient import TestClient
from sqlalchemy import select

from server.db import SearchRecord


def _rows(client: TestClient) -> list[SearchRecord]:
    async def fetch() -> list[SearchRecord]:
        async with client.app.state.db() as session:  # type: ignore[attr-defined]
            return list((await session.scalars(select(SearchRecord))).all())

    return client.portal.call(fetch) if client.portal else asyncio.run(fetch())  # type: ignore[union-attr]


def test_search_is_saved(client: TestClient, roundtrip_body: dict) -> None:
    response = client.post("/api/flights/search", json=roundtrip_body)
    assert response.status_code == 200
    body = response.json()

    saved = [r for r in _rows(client) if r.search_id == body["searchId"]]
    assert len(saved) == 1
    row = saved[0]
    assert (row.origin, row.destination, row.trip_type) == ("LOS", "LHR", "roundtrip")
    assert row.depart_date.isoformat() == roundtrip_body["departDate"]
    assert row.return_date is not None and row.return_date.isoformat() == roundtrip_body["returnDate"]
    assert (row.adults, row.children, row.infants, row.cabin) == (1, 0, 0, "economy")
    assert row.result_count == body["meta"]["count"]
    assert row.provider == "mock"
    assert row.created_at is not None


def test_invalid_search_is_not_saved(client: TestClient, roundtrip_body: dict) -> None:
    before = len(_rows(client))
    response = client.post("/api/flights/search", json={**roundtrip_body, "destination": "LOS"})
    assert response.status_code == 400
    assert len(_rows(client)) == before
