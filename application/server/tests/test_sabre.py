import base64
from datetime import date, timedelta

import httpx
import pytest

from server.config import Settings
from server.errors import ProviderAuthError, ProviderError
from server.providers.sabre import SabreProvider, basic_auth_header, build_search_request
from server.schemas import Passengers, SearchRequest


def _query() -> SearchRequest:
    return SearchRequest(
        trip_type="roundtrip",
        origin="LOS",
        destination="LHR",
        depart_date=date.today() + timedelta(days=10),
        return_date=date.today() + timedelta(days=17),
        passengers=Passengers(adults=2, children=1, infants=1),
        cabin="business",
        currency="GBP",
    )


def test_basic_auth_header_double_encodes() -> None:
    header = basic_auth_header("id", "secret")
    inner = base64.b64decode(header.removeprefix("Basic ")).decode()
    encoded_id, encoded_secret = inner.split(":")
    assert base64.b64decode(encoded_id) == b"id"
    assert base64.b64decode(encoded_secret) == b"secret"


def test_build_search_request_matches_bfm_shape() -> None:
    rq = build_search_request(_query(), "ABC1")["OTA_AirLowFareSearchRQ"]
    legs = rq["OriginDestinationInformation"]
    assert [leg["RPH"] for leg in legs] == ["1", "2"]
    assert legs[0]["OriginLocation"]["LocationCode"] == "LOS"
    assert legs[1]["OriginLocation"]["LocationCode"] == "LHR"
    assert legs[0]["DepartureDateTime"].endswith("T00:00:00")
    assert rq["POS"]["Source"][0] == {
        "PseudoCityCode": "ABC1",
        "RequestorID": {"Type": "1", "ID": "1", "CompanyName": {"Code": "TN"}},
    }
    assert rq["TravelerInfoSummary"]["AirTravelerAvail"][0]["PassengerTypeQuantity"] == [
        {"Code": "ADT", "Quantity": 2},
        {"Code": "CNN", "Quantity": 1},
        {"Code": "INF", "Quantity": 1},
    ]
    assert rq["TravelerInfoSummary"]["PriceRequestInformation"] == {"CurrencyCode": "GBP"}
    assert rq["TravelPreferences"]["CabinPref"] == [{"Cabin": "C", "PreferLevel": "Preferred"}]
    assert rq["TPA_Extensions"]["IntelliSellTransaction"]["RequestType"]["Name"] == "50ITINS"


def _provider(handler) -> SabreProvider:
    settings = Settings(
        sabre_client_id="id", sabre_client_secret="secret", sabre_pcc="PCC1", sabre_base_url="https://sabre.test", _env_file=None  # pyright: ignore[reportCallIssue]
    )
    return SabreProvider(httpx.AsyncClient(transport=httpx.MockTransport(handler)), settings)


async def test_auth_failure_maps_to_provider_auth_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "invalid_client"})

    with pytest.raises(ProviderAuthError):
        await _provider(handler).search(_query())


async def test_shop_failure_maps_to_provider_error_and_token_is_cached() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path == "/v2/auth/token":
            assert request.headers["Authorization"] == basic_auth_header("id", "secret")
            assert request.content == b"grant_type=client_credentials"
            return httpx.Response(200, json={"access_token": "tok", "expires_in": 1800})
        assert request.headers["Authorization"] == "Bearer tok"
        return httpx.Response(500, json={"message": "boom"})

    provider = _provider(handler)
    with pytest.raises(ProviderError):
        await provider.search(_query())
    with pytest.raises(ProviderError):
        await provider.search(_query())
    assert calls.count("/v2/auth/token") == 1
