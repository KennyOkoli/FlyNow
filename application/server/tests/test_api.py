from datetime import date, timedelta

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "provider": "mock"}


def test_airports_lagos_first(client: TestClient) -> None:
    response = client.get("/api/airports", params={"q": "lag"})
    assert response.status_code == 200
    body = response.json()
    assert body[0] == {
        "iata": "LOS",
        "name": "Murtala Muhammed International Airport",
        "city": "Lagos",
        "country": "Nigeria",
    }
    assert len(body) <= 8


def test_airports_exact_code_limit_and_empty(client: TestClient) -> None:
    assert client.get("/api/airports", params={"q": "lhr"}).json()[0]["iata"] == "LHR"
    assert len(client.get("/api/airports", params={"q": "a", "limit": 50}).json()) == 20
    assert client.get("/api/airports", params={"q": ""}).json() == []


def test_search_same_origin_destination_is_validation_error(client: TestClient, roundtrip_body: dict) -> None:
    response = client.post("/api/flights/search", json={**roundtrip_body, "destination": "LOS"})
    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert "differ" in body["error"]["message"]
    assert set(body) == {"error"} and set(body["error"]) == {"code", "message"}


def test_search_return_before_depart_is_validation_error(client: TestClient, roundtrip_body: dict) -> None:
    early = (date.fromisoformat(roundtrip_body["departDate"]) - timedelta(days=1)).isoformat()
    response = client.post("/api/flights/search", json={**roundtrip_body, "returnDate": early})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


def test_search_other_rules(client: TestClient, roundtrip_body: dict) -> None:
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    cases = [
        {**roundtrip_body, "departDate": yesterday},
        {**roundtrip_body, "returnDate": None},
        {**roundtrip_body, "origin": "lo"},
        {**roundtrip_body, "passengers": {"adults": 1, "infants": 2}},
        {**roundtrip_body, "passengers": {"adults": 5, "children": 5}},
        {**roundtrip_body, "cabin": "deluxe"},
    ]
    for body in cases:
        response = client.post("/api/flights/search", json=body)
        assert response.status_code == 400, body
        assert response.json()["error"]["code"] == "validation_error"


def test_search_then_detail(client: TestClient, roundtrip_body: dict) -> None:
    response = client.post("/api/flights/search", json=roundtrip_body)
    assert response.status_code == 200
    body = response.json()
    assert body["searchId"].startswith("srch_")
    assert body["query"] == roundtrip_body
    assert body["currency"] == "USD"
    assert body["meta"]["provider"] == "mock"
    assert body["meta"]["count"] == len(body["itineraries"]) >= 15
    assert body["meta"]["fetchedAt"].endswith("Z")
    referenced_airlines = {
        c for it in body["itineraries"] for leg in it["legs"] for s in leg["segments"] for c in (s["marketingCarrier"], s["operatingCarrier"])
    } | {it["validatingCarrier"] for it in body["itineraries"]}
    referenced_airports = {a for it in body["itineraries"] for leg in it["legs"] for s in leg["segments"] for a in (s["from"], s["to"])}
    assert referenced_airlines <= set(body["airlines"])
    assert referenced_airports <= set(body["airports"])
    assert body["airports"]["LOS"]["city"] == "Lagos"
    first = body["itineraries"][0]
    assert len(first["legs"]) == 2
    assert first["legs"][0]["segments"][0]["layoverMinutes"] is None

    detail = client.get(f"/api/flights/{body['searchId']}/itineraries/{first['id']}")
    assert detail.status_code == 200
    detail_body = detail.json()
    for key in ("id", "price", "legs", "validatingCarrier", "refundable", "cabin", "baggage"):
        assert detail_body[key] == first[key]
    assert detail_body["searchId"] == body["searchId"]
    assert detail_body["query"] == roundtrip_body
    assert detail_body["fareBreakdown"][0]["passengerType"] == "adult"
    assert detail_body["taxes"][0]["code"] == "YQ"
    assert detail_body["fareBasis"] and detail_body["lastTicketDate"]
    assert detail_body["notes"] == [
        "Fares shown are indicative and not guaranteed until ticketed.",
        "Generated sample data, not live fares.",
    ]
    assert set(detail_body["airlines"]) >= {first["validatingCarrier"]}


def test_unknown_search_is_410(client: TestClient) -> None:
    response = client.get("/api/flights/srch_doesnotexist/itineraries/it_1")
    assert response.status_code == 410
    assert response.json()["error"]["code"] == "search_expired"


def test_unknown_itinerary_is_404(client: TestClient, roundtrip_body: dict) -> None:
    search_id = client.post("/api/flights/search", json=roundtrip_body).json()["searchId"]
    response = client.get(f"/api/flights/{search_id}/itineraries/it_999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_unknown_route_uses_error_body(client: TestClient) -> None:
    response = client.get("/api/missing")
    assert response.status_code == 404
    assert response.json() == {"error": {"code": "not_found", "message": "Not Found"}}
