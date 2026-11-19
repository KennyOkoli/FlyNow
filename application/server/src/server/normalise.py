from collections.abc import Iterable
from datetime import date, datetime, time, timedelta
from typing import Any

from server.providers.base import SearchResult
from server.schemas import (
    Baggage,
    Cabin,
    FareBreakdownItem,
    Itinerary,
    ItineraryDetailFields,
    Leg,
    PassengerType,
    Price,
    Segment,
    TaxItem,
)

CABIN_CODES: dict[str, Cabin] = {
    "Y": "economy",
    "S": "premium_economy",
    "C": "business",
    "J": "business",
    "F": "first",
    "P": "first",
}
PASSENGER_TYPES: dict[str, PassengerType] = {"ADT": "adult", "CNN": "child", "INF": "infant"}
PASSENGER_TYPES_REVERSE: dict[PassengerType, str] = {v: k for k, v in PASSENGER_TYPES.items()}

JsonDict = dict[str, Any]


def _by_id(items: Iterable[JsonDict] | None) -> dict[int, JsonDict]:
    return {item["id"]: item for item in items or []}


def _local_datetime(day: date, value: str) -> datetime:
    # Sabre gives "08:25:00+05:30": a wall-clock time plus the airport's offset; combine keeps that offset as-is.
    return datetime.combine(day, time.fromisoformat(value))


def _minutes_between(start: datetime, end: datetime) -> int:
    return int((end - start).total_seconds() // 60)


def _baggage_text(allowance: JsonDict | None) -> str | None:
    if not allowance:
        return None
    if allowance.get("weight") is not None and allowance.get("unit"):
        return f"{allowance['weight']} {str(allowance['unit']).lower()}"
    pieces = allowance.get("pieceCount")
    if pieces is not None:
        return f"{pieces} piece" if pieces == 1 else f"{pieces} pieces"
    return None


def _money(value: Any) -> float:
    return round(float(value or 0), 2)


def _base_amount(fare: JsonDict) -> float:
    # baseFareAmount may be in a different currency than the total (e.g. USD base, BDT total);
    # equivalentAmount is the base already converted into the total's currency.
    if fare.get("baseFareCurrency") and fare.get("baseFareCurrency") != fare.get("currency"):
        if fare.get("equivalentAmount") is not None:
            return _money(fare["equivalentAmount"])
        return _money(float(fare.get("totalPrice", fare.get("totalFare", 0))) - float(fare.get("totalTaxAmount", 0)))
    return _money(fare.get("baseFareAmount"))


def _tidy_description(text: str | None, fallback: str) -> str:
    if not text:
        return fallback
    return text.capitalize() if not any(c.islower() for c in text) else text


class Normaliser:
    def __init__(self, gir: JsonDict, passengers: dict[PassengerType, int]) -> None:
        self.schedules = _by_id(gir.get("scheduleDescs"))
        self.leg_descs = _by_id(gir.get("legDescs"))
        self.tax_summaries = _by_id(gir.get("taxSummaryDescs"))
        self.tax_descs = _by_id(gir.get("taxDescs"))
        self.fare_components = _by_id(gir.get("fareComponentDescs"))
        self.baggage_descs = _by_id(gir.get("baggageAllowanceDescs"))
        self.groups: list[JsonDict] = gir.get("itineraryGroups") or []
        self.passengers = passengers
        self.airline_codes: set[str] = set()
        self.airport_codes: set[str] = set()
        self._leg_counter = 0

    def run(self) -> SearchResult:
        itineraries: list[Itinerary] = []
        details: dict[str, ItineraryDetailFields] = {}
        for group in self.groups:
            leg_dates = [
                date.fromisoformat(d["departureDate"])
                for d in group.get("groupDescription", {}).get("legDescriptions", [])
            ]
            for raw in group.get("itineraries", []):
                itin_id = f"it_{len(itineraries) + 1}"
                itinerary, detail = self._itinerary(itin_id, raw, leg_dates)
                itineraries.append(itinerary)
                details[itin_id] = detail
        return SearchResult(
            itineraries=itineraries,
            details=details,
            airline_codes=self.airline_codes,
            airport_codes=self.airport_codes,
        )

    def _itinerary(self, itin_id: str, raw: JsonDict, leg_dates: list[date]) -> tuple[Itinerary, ItineraryDetailFields]:
        fare: JsonDict = raw["pricingInformation"][0]["fare"]
        pax_infos: list[JsonDict] = [p["passengerInfo"] for p in fare.get("passengerInfoList", [])]
        adult = next((p for p in pax_infos if p.get("passengerType") == "ADT"), pax_infos[0] if pax_infos else {})

        fare_segments = [
            seg["segment"] for fc in adult.get("fareComponents", []) for seg in fc.get("segments", [])
        ]

        legs: list[Leg] = []
        segment_index = 0
        for leg_index, leg_ref in enumerate(raw.get("legs", [])):
            leg_desc = self.leg_descs[leg_ref["ref"]]
            base_date = leg_dates[leg_index] if leg_index < len(leg_dates) else leg_dates[-1]
            leg, used = self._leg(leg_desc, base_date, fare_segments[segment_index:])
            segment_index += used
            legs.append(leg)

        total_fare: JsonDict = fare.get("totalFare", {})
        adult_fare: JsonDict = adult.get("passengerTotalFare", {})
        currency = total_fare.get("currency") or adult_fare.get("currency") or "USD"
        price = Price(
            total=_money(total_fare.get("totalPrice")),
            base=_base_amount(total_fare),
            taxes=_money(total_fare.get("totalTaxAmount")),
            currency=currency,
            per_adult=_money(adult_fare.get("totalFare", total_fare.get("totalPrice"))),
        )

        validating = fare.get("validatingCarrierCode") or legs[0].segments[0].marketing_carrier
        self.airline_codes.add(validating)

        first_cabin = fare_segments[0].get("cabinCode") if fare_segments else None
        cabin: Cabin = CABIN_CODES.get(first_cabin or "", legs[0].segments[0].cabin)

        seats = [s["seatsAvailable"] for s in fare_segments if s.get("seatsAvailable") is not None]

        baggage_info = adult.get("baggageInformation") or []
        allowance = baggage_info[0].get("allowance") if baggage_info else None
        if allowance and "ref" in allowance:
            allowance = self.baggage_descs.get(allowance["ref"])

        itinerary = Itinerary(
            id=itin_id,
            price=price,
            validating_carrier=validating,
            refundable=not adult.get("nonRefundable", True),
            seats_left=min(seats) if seats else None,
            cabin=cabin,
            baggage=Baggage(checked=_baggage_text(allowance)),
            legs=legs,
        )
        detail = ItineraryDetailFields(
            fare_breakdown=[self._fare_breakdown(p) for p in pax_infos if p.get("passengerType") in PASSENGER_TYPES],
            taxes=self._taxes(adult),
            last_ticket_date=date.fromisoformat(fare["lastTicketDate"]) if fare.get("lastTicketDate") else None,
            fare_basis=self._fare_basis(adult),
        )
        return itinerary, detail

    def _leg(self, leg_desc: JsonDict, base_date: date, fare_segments: list[JsonDict]) -> tuple[Leg, int]:
        self._leg_counter += 1
        segments: list[Segment] = []
        for index, entry in enumerate(leg_desc.get("schedules", [])):
            schedule = self.schedules[entry["ref"]]
            fare_seg = fare_segments[index] if index < len(fare_segments) else {}
            depart_day = base_date + timedelta(days=entry.get("departureDateAdjustment", 0))
            depart_at = _local_datetime(depart_day, schedule["departure"]["time"])
            arrive_day = depart_day + timedelta(days=schedule["arrival"].get("dateAdjustment", 0))
            arrive_at = _local_datetime(arrive_day, schedule["arrival"]["time"])
            carrier = schedule.get("carrier", {})
            marketing = carrier.get("marketing", "")
            operating = carrier.get("operating") or marketing
            self.airline_codes.update({marketing, operating})
            self.airport_codes.update({schedule["departure"]["airport"], schedule["arrival"]["airport"]})
            segments.append(
                Segment(
                    from_=schedule["departure"]["airport"],
                    to=schedule["arrival"]["airport"],
                    depart_at=depart_at,
                    arrive_at=arrive_at,
                    duration_minutes=schedule.get("elapsedTime") or _minutes_between(depart_at, arrive_at),
                    marketing_carrier=marketing,
                    operating_carrier=operating,
                    flight_number=f"{marketing}{carrier.get('marketingFlightNumber', '')}",
                    aircraft=(carrier.get("equipment") or {}).get("code"),
                    booking_class=fare_seg.get("bookingCode"),
                    cabin=CABIN_CODES.get(fare_seg.get("cabinCode", ""), "economy"),
                    departure_terminal=schedule["departure"].get("terminal"),
                    arrival_terminal=schedule["arrival"].get("terminal"),
                    layover_minutes=None if index == 0 else _minutes_between(segments[-1].arrive_at, depart_at),
                )
            )
        carriers: list[str] = []
        for seg in segments:
            if seg.marketing_carrier not in carriers:
                carriers.append(seg.marketing_carrier)
        leg = Leg(
            id=f"leg_{self._leg_counter}",
            from_=segments[0].from_,
            to=segments[-1].to,
            depart_at=segments[0].depart_at,
            arrive_at=segments[-1].arrive_at,
            duration_minutes=leg_desc.get("elapsedTime") or _minutes_between(segments[0].depart_at, segments[-1].arrive_at),
            stops=len(segments) - 1,
            carriers=carriers,
            segments=segments,
        )
        return leg, len(segments)

    def _fare_breakdown(self, pax: JsonDict) -> FareBreakdownItem:
        pax_type = PASSENGER_TYPES[pax["passengerType"]]
        fare: JsonDict = pax.get("passengerTotalFare", {})
        return FareBreakdownItem(
            passenger_type=pax_type,
            count=pax.get("passengerNumber") or self.passengers.get(pax_type, 1),
            base=_base_amount(fare),
            taxes=_money(fare.get("totalTaxAmount")),
            total=_money(fare.get("totalFare")),
        )

    def _taxes(self, pax: JsonDict) -> list[TaxItem]:
        descriptions = {t["code"]: t.get("description") for t in self.tax_descs.values() if t.get("code")}
        taxes: list[TaxItem] = []
        for ref in pax.get("taxSummaries", []):
            summary = self.tax_summaries.get(ref["ref"])
            if summary is None:
                continue
            code = summary.get("code", "")
            taxes.append(
                TaxItem(
                    code=code,
                    amount=_money(summary.get("amount")),
                    description=_tidy_description(descriptions.get(code), summary.get("description") or code),
                )
            )
        return taxes

    def _fare_basis(self, pax: JsonDict) -> list[str]:
        codes: list[str] = []
        for fc in pax.get("fareComponents", []):
            desc = self.fare_components.get(fc.get("ref"))
            code = desc.get("fareBasisCode") if desc else None
            if code and code not in codes:
                codes.append(code)
        return codes


def normalise(gir: JsonDict, passengers: dict[PassengerType, int]) -> SearchResult:
    return Normaliser(gir, passengers).run()
