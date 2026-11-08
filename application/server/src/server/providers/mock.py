import hashlib
import math
import random
from datetime import UTC, date, datetime, timedelta, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from server.data import airports_by_iata
from server.providers.base import ProviderName, SearchResult
from server.schemas import (
    Baggage,
    Cabin,
    FareBreakdownItem,
    Itinerary,
    ItineraryDetailFields,
    Leg,
    Price,
    SearchRequest,
    Segment,
    TaxItem,
)

# Fixed conversion from the USD base; not a live rate.
USD_RATES: dict[str, float] = {
    "USD": 1.0,
    "NGN": 1550.0,
    "EUR": 0.92,
    "GBP": 0.78,
    "CAD": 1.38,
    "GHS": 15.5,
    "KES": 129.0,
    "ZAR": 18.2,
    "AED": 3.67,
}
CABIN_MULTIPLIER: dict[Cabin, float] = {"economy": 1.0, "premium_economy": 1.7, "business": 3.2, "first": 5.0}
STOPS_MULTIPLIER: dict[int, float] = {0: 1.2, 1: 1.0, 2: 0.88}
BOOKING_CLASSES: dict[Cabin, str] = {"economy": "YBHKLMNOQSV", "premium_economy": "WET", "business": "JCDI", "first": "FAP"}

NIGERIA_CARRIERS = ("W3", "P4", "Q9", "9J", "VL")
HUBS: dict[str, tuple[str, ...]] = {
    "ET": ("ADD",),
    "TK": ("IST",),
    "QR": ("DOH",),
    "EK": ("DXB",),
    "AF": ("CDG",),
    "KL": ("AMS",),
    "BA": ("LHR",),
    "VS": ("LHR",),
    "LH": ("FRA", "MUC"),
    "KQ": ("NBO",),
    "AT": ("CMN",),
    "MS": ("CAI",),
    "DL": ("ATL", "JFK"),
    "UA": ("EWR", "IAD"),
    "SA": ("JNB",),
    "WB": ("KGL",),
}
TERMINALS: dict[str, dict[str, str | None]] = {
    "LOS": {"*": "I", "domestic": "2"},
    "ABV": {"*": "I", "domestic": "D"},
    "LHR": {"BA": "5", "VS": "3", "*": "4"},
    "LGW": {"*": "S"},
    "CDG": {"AF": "2E", "*": "2A"},
    "AMS": {"*": None},
    "FRA": {"*": "1"},
    "MUC": {"*": "2"},
    "IST": {"*": None},
    "DOH": {"*": None},
    "DXB": {"EK": "3", "*": "1"},
    "ADD": {"*": "2"},
    "NBO": {"*": "1A"},
    "CAI": {"*": "3"},
    "CMN": {"*": "2"},
    "JFK": {"DL": "4", "BA": "7", "VS": "4", "*": "8"},
    "ATL": {"*": "I"},
    "EWR": {"*": "C"},
    "IAD": {"*": None},
    "JNB": {"*": "A"},
    "KGL": {"*": None},
}
SHORT_HAUL_AIRCRAFT = ("737", "738", "320", "319", "321", "E90", "73H")
MEDIUM_HAUL_AIRCRAFT = ("321", "738", "32N", "788", "332", "333")
LONG_HAUL_AIRCRAFT = ("777", "77W", "788", "789", "359", "333", "332", "351")
TAX_CODES: dict[str, tuple[tuple[str, str], ...]] = {
    "Nigeria": (("QT", "Passenger service charge"), ("TE", "Ticket sales charge")),
    "United Kingdom": (("GB", "Air passenger duty"), ("UB", "Passenger service charge")),
    "United States": (("US", "Transportation tax"), ("XY", "Immigration user fee")),
    "France": (("FR", "Civil aviation tax"), ("QX", "Passenger service charge")),
    "Germany": (("DE", "Air transport tax"), ("RA", "Aviation security fee")),
    "Ghana": (("GH", "Airport passenger service charge"), ("YA", "Security charge")),
    "Kenya": (("KE", "Airport service charge"), ("RW", "Security fee")),
    "South Africa": (("ZA", "Air passenger tax"), ("EV", "Passenger service charge")),
}
DEFAULT_TAX_CODES = (("XT", "Airport taxes and fees"),)
MAX_DETOUR = 2.0
DEPARTURE_HOURS = (6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 19, 21, 22, 23)


def _zone(code: str) -> tzinfo:
    record = airports_by_iata().get(code)
    try:
        tz = record.get("tz") if record else None
        return ZoneInfo(tz) if tz else UTC
    except ZoneInfoNotFoundError:
        return UTC


def _country(code: str) -> str:
    record = airports_by_iata().get(code)
    return record["country"] if record else ""


def great_circle_km(origin: str, destination: str) -> float:
    a = airports_by_iata().get(origin)
    b = airports_by_iata().get(destination)
    coords = (a.get("lat"), a.get("lon"), b.get("lat"), b.get("lon")) if a and b else None
    if coords is None or None in coords:
        return 3000.0
    lat1, lon1, lat2, lon2 = (math.radians(c) for c in coords if c is not None)
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(h))


def _detour(origin: str, via: str, destination: str) -> float:
    return great_circle_km(origin, via) + great_circle_km(via, destination)


def _flight_minutes(km: float) -> int:
    return int(30 + km / 13.5)


def _aircraft(rng: random.Random, km: float, carrier: str) -> str:
    if km < 1500:
        return rng.choice(SHORT_HAUL_AIRCRAFT)
    if km < 4000:
        return rng.choice(MEDIUM_HAUL_AIRCRAFT)
    if carrier == "EK":
        return rng.choice(("388", "77W"))
    return rng.choice(LONG_HAUL_AIRCRAFT)


def _terminal(airport: str, carrier: str, domestic: bool) -> str | None:
    table = TERMINALS.get(airport)
    if table is None:
        return None
    if domestic and "domestic" in table:
        return table["domestic"]
    return table.get(carrier, table.get("*"))


def _money(value: float) -> float:
    return round(value, 2)


class MockProvider:
    name: ProviderName = "mock"

    async def search(self, query: SearchRequest) -> SearchResult:
        return MockSearch(query).run()


class MockSearch:
    def __init__(self, query: SearchRequest) -> None:
        self.query = query
        seed_source = f"{query.origin}|{query.destination}|{query.depart_date}|{query.return_date}|{query.cabin}"
        self.rng = random.Random(int(hashlib.sha256(seed_source.encode()).hexdigest(), 16))
        self.domestic = (
            _country(query.origin) == "Nigeria" and _country(query.destination) == "Nigeria"
        )
        self.rate = USD_RATES.get(query.currency, 1.0)
        self.airline_codes: set[str] = set()
        self.airport_codes: set[str] = set()
        self._leg_counter = 0

    def run(self) -> SearchResult:
        count = self.rng.randint(15, 25)
        itineraries: list[Itinerary] = []
        details: dict[str, ItineraryDetailFields] = {}
        drafts = [self._draft() for _ in range(count)]
        drafts.sort(key=lambda d: d[0].price.total)
        leg_counter = 0
        for index, (itinerary, detail) in enumerate(drafts, start=1):
            itinerary.id = f"it_{index}"
            for leg in itinerary.legs:
                leg_counter += 1
                leg.id = f"leg_{leg_counter}"
            itineraries.append(itinerary)
            details[itinerary.id] = detail
        return SearchResult(
            itineraries=itineraries,
            details=details,
            airline_codes=self.airline_codes,
            airport_codes=self.airport_codes,
        )

    def _route(self) -> list[tuple[str, str]]:
        """Pick (carrier, next airport) hops from origin to destination."""
        origin, destination = self.query.origin, self.query.destination
        if self.domestic:
            return [(self.rng.choice(NIGERIA_CARRIERS), destination)]

        roll = self.rng.random()
        endpoints = {origin, destination}
        nonstop_carriers = [c for c, hubs in HUBS.items() if endpoints & set(hubs)]
        direct_km = great_circle_km(origin, destination)
        connecting = [
            c for c in HUBS
            if c not in nonstop_carriers and any(_detour(origin, hub, destination) <= MAX_DETOUR * direct_km for hub in HUBS[c])
        ]
        if len(connecting) < 3:
            connecting = [c for c in HUBS if c not in nonstop_carriers]

        if roll < 0.25:
            carrier = self.rng.choice(nonstop_carriers or list(HUBS))
            return [(carrier, destination)]
        if roll < 0.75 or len(connecting) < 2:
            carrier = self.rng.choice(connecting)
            hub = self.rng.choice(HUBS[carrier])
            return [(carrier, hub), (carrier, destination)]
        first, second = self.rng.sample(connecting, 2)
        hub_a = self.rng.choice(HUBS[first])
        hub_b = self.rng.choice([h for h in HUBS[second] if h != hub_a] or HUBS[second])
        return [(first, hub_a), (second, hub_b), (second, destination)]

    def _draft(self) -> tuple[Itinerary, ItineraryDetailFields]:
        route = self._route()
        cabin = self.query.cabin
        booking_class = self.rng.choice(BOOKING_CLASSES[cabin])
        legs = [self._leg(self.query.origin, route, self.query.depart_date, booking_class)]
        if self.query.trip_type == "roundtrip" and self.query.return_date is not None:
            inbound_stops = [stop for _, stop in route[:-1]][::-1] + [self.query.origin]
            inbound_route = list(zip([carrier for carrier, _ in route][::-1], inbound_stops))
            legs.append(self._leg(self.query.destination, inbound_route, self.query.return_date, booking_class))

        km = great_circle_km(self.query.origin, self.query.destination) * len(legs)
        stops = len(route) - 1
        fare_usd = (45 + 0.09 * km) * CABIN_MULTIPLIER[cabin] * STOPS_MULTIPLIER[stops]
        if self.query.trip_type == "roundtrip":
            fare_usd *= 0.9
        fare_usd *= self.rng.uniform(0.85, 1.25)
        tax_ratio = self.rng.uniform(0.25, 0.4) if cabin in ("economy", "premium_economy") else self.rng.uniform(0.12, 0.22)

        adult_base = _money(fare_usd * self.rate)
        adult_taxes = _money(fare_usd * tax_ratio * self.rate)
        child_base = _money(adult_base * 0.75)
        infant_base = _money(adult_base * 0.1)
        pax = self.query.passengers
        breakdown = [FareBreakdownItem(passenger_type="adult", count=pax.adults, base=adult_base, taxes=adult_taxes, total=_money(adult_base + adult_taxes))]
        if pax.children:
            breakdown.append(FareBreakdownItem(passenger_type="child", count=pax.children, base=child_base, taxes=adult_taxes, total=_money(child_base + adult_taxes)))
        if pax.infants:
            breakdown.append(FareBreakdownItem(passenger_type="infant", count=pax.infants, base=infant_base, taxes=0.0, total=infant_base))
        base_total = _money(sum(item.base * item.count for item in breakdown))
        tax_total = _money(sum(item.taxes * item.count for item in breakdown))

        validating = route[0][0]
        refundable_chance = 0.1 if cabin in ("economy", "premium_economy") else 0.5
        if cabin in ("economy", "premium_economy"):
            baggage = None if (self.domestic and self.rng.random() < 0.15) else self.rng.choice(("23 kg", "23 kg", "1 piece", "2 pieces", "30 kg"))
        else:
            baggage = self.rng.choice(("2 pieces", "32 kg", "40 kg"))

        itinerary = Itinerary(
            id="it_0",
            price=Price(total=_money(base_total + tax_total), base=base_total, taxes=tax_total, currency=self.query.currency, per_adult=breakdown[0].total),
            validating_carrier=validating,
            refundable=self.rng.random() < refundable_chance,
            seats_left=self.rng.choice((1, 2, 3, 4, 5, 6, 7, 9, 9, 9)),
            cabin=cabin,
            baggage=Baggage(checked=baggage),
            legs=legs,
        )
        detail = ItineraryDetailFields(
            fare_breakdown=breakdown,
            taxes=self._taxes(adult_taxes),
            last_ticket_date=self._last_ticket_date(),
            fare_basis=[self._fare_basis(booking_class)],
        )
        return itinerary, detail

    def _leg(self, origin: str, route: list[tuple[str, str]], day: date, booking_class: str) -> Leg:
        self._leg_counter += 1
        segments: list[Segment] = []
        current = origin
        depart_at = datetime(day.year, day.month, day.day, self.rng.choice(DEPARTURE_HOURS), self.rng.choice((0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55)), tzinfo=_zone(origin))
        layover: int | None = None
        for carrier, stop in route:
            km = great_circle_km(current, stop)
            minutes = _flight_minutes(km)
            arrive_at = (depart_at + timedelta(minutes=minutes)).astimezone(_zone(stop))
            self.airline_codes.add(carrier)
            self.airport_codes.update({current, stop})
            segments.append(
                Segment(
                    from_=current,
                    to=stop,
                    depart_at=depart_at,
                    arrive_at=arrive_at,
                    duration_minutes=minutes,
                    marketing_carrier=carrier,
                    operating_carrier=carrier,
                    flight_number=f"{carrier}{self.rng.randint(100, 999) if km > 1500 else self.rng.randint(100, 899)}",
                    aircraft=_aircraft(self.rng, km, carrier),
                    booking_class=booking_class,
                    cabin=self.query.cabin,
                    departure_terminal=_terminal(current, carrier, self.domestic),
                    arrival_terminal=_terminal(stop, carrier, self.domestic),
                    layover_minutes=layover,
                )
            )
            layover = self.rng.randrange(60, 361, 5)
            depart_at = arrive_at + timedelta(minutes=layover)
            current = stop
        carriers: list[str] = []
        for seg in segments:
            if seg.marketing_carrier not in carriers:
                carriers.append(seg.marketing_carrier)
        return Leg(
            id=f"leg_{self._leg_counter}",
            from_=origin,
            to=current,
            depart_at=segments[0].depart_at,
            arrive_at=segments[-1].arrive_at,
            duration_minutes=int((segments[-1].arrive_at - segments[0].depart_at).total_seconds() // 60),
            stops=len(segments) - 1,
            carriers=carriers,
            segments=segments,
        )

    def _taxes(self, adult_taxes: float) -> list[TaxItem]:
        codes = list(TAX_CODES.get(_country(self.query.origin), DEFAULT_TAX_CODES))
        codes += [c for c in TAX_CODES.get(_country(self.query.destination), DEFAULT_TAX_CODES) if c not in codes]
        shares = [self.rng.uniform(0.05, 0.15) for _ in codes]
        items = [TaxItem(code=code, amount=_money(adult_taxes * share), description=desc) for (code, desc), share in zip(codes, shares)]
        surcharge = _money(adult_taxes - sum(item.amount for item in items))
        return [TaxItem(code="YQ", amount=surcharge, description="Carrier-imposed surcharge"), *items]

    def _last_ticket_date(self) -> date:
        today = date.today()
        candidate = min(self.query.depart_date - timedelta(days=7), today + timedelta(days=3))
        return max(candidate, today)

    def _fare_basis(self, booking_class: str) -> str:
        return f"{booking_class}{self.rng.choice('LHKQ')}{self.rng.choice('XNW')}{self.rng.randint(1, 9)}{self.rng.choice(('AF', 'NG', 'UK', 'RT', 'OW'))}"

