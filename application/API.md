# Flights app — API contract

The Vue app never calls Sabre. It calls this FastAPI server, which calls Sabre (or a mock provider) and returns the normalised shapes below. Both halves are built against this file; change it here first.

Server: `http://127.0.0.1:8000`. Vite proxies `/api/*` to it in dev.

## Conventions

- JSON everywhere. Times are ISO 8601 **local to the airport**, with offset, e.g. `2026-12-10T08:25:00+01:00`.
- Money is a number in minor-free units (e.g. `412.50`) with a separate `currency` ISO code.
- Errors: HTTP 4xx/5xx with body `{ "error": { "code": "string", "message": "human readable" } }`. Codes: `validation_error` (400), `not_found` (404), `search_expired` (410), `provider_error` (502), `provider_auth_error` (502).
- Search results are kept in server memory for 30 minutes under `searchId`; the detail endpoint reads from that cache.

## GET /api/health

`200 { "status": "ok", "provider": "sabre" | "mock" }`

## GET /api/airports?q=lag&limit=8

Autocomplete over the bundled airport list. Matches IATA code (exact first), city, airport name; case-insensitive; `limit` default 8, max 20.

```json
[{ "iata": "LOS", "name": "Murtala Muhammed International Airport", "city": "Lagos", "country": "Nigeria" }]
```

## POST /api/flights/search

Request:

```json
{
  "tripType": "oneway" | "roundtrip",
  "origin": "LOS",
  "destination": "LHR",
  "departDate": "2026-12-10",
  "returnDate": "2026-12-20",
  "passengers": { "adults": 1, "children": 0, "infants": 0 },
  "cabin": "economy" | "premium_economy" | "business" | "first",
  "currency": "USD"
}
```

Rules: IATA codes are 3 uppercase letters and must differ; dates are `YYYY-MM-DD`, departDate today or later, returnDate required for roundtrip and not before departDate; adults 1–9, children 0–8, infants 0–adults; total passengers ≤ 9. `currency` optional, default `USD`.

Response `200`:

```json
{
  "searchId": "srch_8f3a...",
  "query": { ...request echoed back... },
  "currency": "USD",
  "itineraries": [Itinerary],
  "airlines": { "BA": "British Airways" },
  "airports": { "LOS": { "city": "Lagos", "name": "Murtala Muhammed International Airport", "country": "Nigeria" } },
  "meta": { "count": 23, "provider": "sabre" | "mock", "fetchedAt": "2026-11-08T12:00:00Z" }
}
```

`airlines` and `airports` contain every code referenced in `itineraries`, so the UI never needs another lookup.

### Itinerary

```json
{
  "id": "it_1",
  "price": { "total": 612.40, "base": 420.00, "taxes": 192.40, "currency": "USD", "perAdult": 612.40 },
  "validatingCarrier": "BA",
  "refundable": false,
  "seatsLeft": 4,
  "cabin": "economy",
  "baggage": { "checked": "23 kg" | "1 piece" | "2 pieces" | null },
  "legs": [Leg]
}
```

`legs` has 1 entry for oneway, 2 for roundtrip (outbound, inbound). `seatsLeft` is the minimum across segments, null if unknown. `baggage.checked` is a short display string or null if the provider gave nothing.

### Leg

```json
{
  "id": "leg_1",
  "from": "LOS",
  "to": "LHR",
  "departAt": "2026-12-10T22:30:00+01:00",
  "arriveAt": "2026-12-11T05:40:00+00:00",
  "durationMinutes": 430,
  "stops": 0,
  "carriers": ["BA"],
  "segments": [Segment]
}
```

`carriers` is the ordered unique list of marketing carriers. `stops` = segments.length − 1.

### Segment

```json
{
  "from": "LOS",
  "to": "LHR",
  "departAt": "2026-12-10T22:30:00+01:00",
  "arriveAt": "2026-12-11T05:40:00+00:00",
  "durationMinutes": 430,
  "marketingCarrier": "BA",
  "operatingCarrier": "BA",
  "flightNumber": "BA74",
  "aircraft": "777",
  "bookingClass": "O",
  "cabin": "economy",
  "departureTerminal": "I",
  "arrivalTerminal": "5",
  "layoverMinutes": null
}
```

`layoverMinutes` is the wait **before** this segment (null on the first segment of a leg). Terminals are null when unknown.

## GET /api/flights/{searchId}/itineraries/{itineraryId}

Returns the full `Itinerary` from the cached search plus detail fields:

```json
{
  ...Itinerary,
  "searchId": "srch_8f3a...",
  "query": { ...the original search request... },
  "airlines": { ... }, "airports": { ... },
  "fareBreakdown": [  // base, taxes and total are per passenger of that type
    { "passengerType": "adult" | "child" | "infant", "count": 1, "base": 420.00, "taxes": 192.40, "total": 612.40 }
  ],
  "taxes": [{ "code": "YQ", "amount": 150.00, "description": "Carrier-imposed surcharge" }],
  "lastTicketDate": "2026-12-03",
  "fareBasis": ["OLX2AF"],
  "notes": ["Fares shown are indicative and not guaranteed until ticketed."]
}
```

`404 not_found` if the itinerary id isn't in that search; `410 search_expired` if the search id is unknown or older than 30 minutes (the UI should offer to re-run the search).

## Provider notes (server only)

- Env: `SABRE_CLIENT_ID`, `SABRE_CLIENT_SECRET`, `SABRE_PCC`, `SABRE_BASE_URL` (default `https://api.cert.platform.sabre.com`), `USE_MOCK` (default `true` when credentials are missing). Never log credentials.
- Auth: `POST {base}/v2/auth/token`, header `Authorization: Basic base64( base64(client_id) + ":" + base64(client_secret) )`, body `grant_type=client_credentials`. Cache the token until `expires_in` − 60s.
- Search: `POST {base}/v2/offers/shop` with `OTA_AirLowFareSearchRQ` (see `server/src/server/data/sabre_bfm_postman_collection.json`, request "BargainFinderMax_GIR_JSON_basic"). Response shape: `server/src/server/data/sabre_bfm_sample_response.json` (`groupedItineraryResponse` with `scheduleDescs`, `legDescs`, `itineraryGroups`, `fareComponentDescs`, `baggageAllowanceDescs`, `taxDescs`).
- Cabin → Sabre: economy `Y`, premium_economy `S`, business `C`, first `F`. Passengers → `ADT`, `CNN`, `INF`.
