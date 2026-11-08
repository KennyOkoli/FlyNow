import os
from collections.abc import Iterator
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

os.environ["USE_MOCK"] = "true"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from server.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def depart_date() -> str:
    return (date.today() + timedelta(days=30)).isoformat()


@pytest.fixture
def return_date() -> str:
    return (date.today() + timedelta(days=40)).isoformat()


@pytest.fixture
def roundtrip_body(depart_date: str, return_date: str) -> dict:
    return {
        "tripType": "roundtrip",
        "origin": "LOS",
        "destination": "LHR",
        "departDate": depart_date,
        "returnDate": return_date,
        "passengers": {"adults": 1, "children": 0, "infants": 0},
        "cabin": "economy",
        "currency": "USD",
    }
