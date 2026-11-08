import base64
from httpx._models import Response
import logging
import time
from typing import Any

import httpx

from server.config import Settings
from server.errors import ProviderAuthError, ProviderError
from server.normalise import PASSENGER_TYPES_REVERSE, normalise
from server.providers.base import ProviderName, SearchResult
from server.schemas import Cabin, PassengerType, SearchRequest

logger = logging.getLogger(__name__)

SABRE_CABIN: dict[Cabin, str] = {"economy": "Y", "premium_economy": "S", "business": "C", "first": "F"}
TOKEN_SAFETY_SECONDS = 60


def build_search_request(query: SearchRequest, pcc: str) -> dict[str, Any]:
    legs = [(query.origin, query.destination, query.depart_date)]
    if query.trip_type == "roundtrip" and query.return_date is not None:
        legs.append((query.destination, query.origin, query.return_date))

    quantities = [{"Code": "ADT", "Quantity": query.passengers.adults}]
    if query.passengers.children:
        quantities.append({"Code": PASSENGER_TYPES_REVERSE["child"], "Quantity": query.passengers.children})
    if query.passengers.infants:
        quantities.append({"Code": PASSENGER_TYPES_REVERSE["infant"], "Quantity": query.passengers.infants})

    traveler_info: dict[str, Any] = {"AirTravelerAvail": [{"PassengerTypeQuantity": quantities}]}
    if query.currency:
        traveler_info["PriceRequestInformation"] = {"CurrencyCode": query.currency}

    return {
        "OTA_AirLowFareSearchRQ": {
            "Version": "5",
            "POS": {
                "Source": [
                    {
                        "PseudoCityCode": pcc,
                        "RequestorID": {"Type": "1", "ID": "1", "CompanyName": {"Code": "TN"}},
                    }
                ]
            },
            "OriginDestinationInformation": [
                {
                    "RPH": str(index),
                    "DepartureDateTime": f"{day.isoformat()}T00:00:00",
                    "OriginLocation": {"LocationCode": origin},
                    "DestinationLocation": {"LocationCode": destination},
                }
                for index, (origin, destination, day) in enumerate(legs, start=1)
            ],
            "TravelPreferences": {"CabinPref": [{"Cabin": SABRE_CABIN[query.cabin], "PreferLevel": "Preferred"}]},
            "TravelerInfoSummary": traveler_info,
            "TPA_Extensions": {"IntelliSellTransaction": {"RequestType": {"Name": "50ITINS"}}},
        }
    }


def basic_auth_header(client_id: str, client_secret: str) -> str:
    # Sabre wants each credential base64-encoded on its own before the pair is base64-encoded again.
    encoded_id = base64.b64encode(client_id.encode()).decode()
    encoded_secret = base64.b64encode(client_secret.encode()).decode()
    pair = base64.b64encode(f"{encoded_id}:{encoded_secret}".encode()).decode()
    return f"Basic {pair}"


class SabreProvider:
    name: ProviderName = "sabre"

    def __init__(self, client: httpx.AsyncClient, settings: Settings) -> None:
        self._client = client
        self._settings = settings
        self._token: str | None = None
        self._token_expires_at: float = 0.0

    async def _get_token(self) -> str:
        if self._token and time.monotonic() < self._token_expires_at:
            return self._token
        headers = {
            "Authorization": basic_auth_header(
                self._settings.resolved_client_id,
                self._settings.resolved_client_secret,
            ),
            "Content-Type": "application/x-www-form-urlencoded",
        }
        try:
            response: Response = await self._client.post(
                f"{self._settings.sabre_base_url}/v2/auth/token",
                headers=headers,
                data={"grant_type": "client_credentials"},
            )
        except httpx.HTTPError as exc:
            raise ProviderAuthError(f"Could not reach the Sabre auth endpoint: {exc.__class__.__name__}") from exc
        if response.status_code >= 400:
            logger.warning("Sabre auth failed with status %s", response.status_code)
            raise ProviderAuthError(f"Sabre authentication failed (HTTP {response.status_code})")
        payload = response.json()
        token = payload.get("access_token")
        if not token:
            raise ProviderAuthError("Sabre authentication response did not include a token")
        self._token = token
        self._token_expires_at = time.monotonic() + max(int(payload.get("expires_in", 0)) - TOKEN_SAFETY_SECONDS, 0)
        return token

    async def search(self, query: SearchRequest) -> SearchResult:
        token = await self._get_token()
        body = build_search_request(query, self._settings.sabre_pcc)
        try:
            response = await self._client.post(
                f"{self._settings.sabre_base_url}/v5/offers/shop",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=body,
            )
        except httpx.HTTPError as exc:
            raise ProviderError(f"Could not reach Sabre: {exc.__class__.__name__}") from exc
        if response.status_code in (401, 403):
            self._token = None
            raise ProviderAuthError(f"Sabre rejected the access token (HTTP {response.status_code})")
        if response.status_code >= 400:
            logger.warning("Sabre shop failed with status %s", response.status_code)
            raise ProviderError(f"Sabre search failed (HTTP {response.status_code}): {_error_text(response)}")

        payload = response.json()
        gir = payload.get("groupedItineraryResponse")
        if gir is None:
            raise ProviderError("Sabre response did not contain groupedItineraryResponse")
        errors = [m.get("text", "") for m in gir.get("messages", []) if m.get("severity") == "Error"]
        if errors and not gir.get("itineraryGroups"):
            raise ProviderError("Sabre returned an error: " + "; ".join(errors))

        passengers: dict[PassengerType, int] = {
            "adult": query.passengers.adults,
            "child": query.passengers.children,
            "infant": query.passengers.infants,
        }
        return normalise(gir, passengers)


def _error_text(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text[:200]
    if isinstance(payload, dict):
        return str(payload.get("message") or payload.get("error_description") or payload)[:200]
    return str(payload)[:200]
