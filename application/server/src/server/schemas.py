from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, PlainSerializer, model_validator
from pydantic.alias_generators import to_camel

TripType = Literal["oneway", "roundtrip"]
Cabin = Literal["economy", "premium_economy", "business", "first"]
PassengerType = Literal["adult", "child", "infant"]

IataCode = Annotated[str, Field(pattern=r"^[A-Z]{3}$")]
LocalDateTime = Annotated[AwareDatetime, PlainSerializer(lambda d: d.isoformat(), return_type=str)]
UtcDateTime = Annotated[
    AwareDatetime,
    PlainSerializer(lambda d: d.strftime("%Y-%m-%dT%H:%M:%SZ"), return_type=str),
]


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, serialize_by_alias=True)


class Passengers(CamelModel):
    adults: int = Field(ge=1, le=9)
    children: int = Field(default=0, ge=0, le=8)
    infants: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def check_totals(self) -> "Passengers":
        if self.infants > self.adults:
            raise ValueError("infants cannot exceed adults")
        if self.adults + self.children + self.infants > 9:
            raise ValueError("total passengers cannot exceed 9")
        return self


class SearchRequest(CamelModel):
    trip_type: TripType
    origin: IataCode
    destination: IataCode
    depart_date: date
    return_date: date | None = None
    passengers: Passengers
    cabin: Cabin = "economy"
    currency: Annotated[str, Field(pattern=r"^[A-Z]{3}$")] = "USD"

    @model_validator(mode="after")
    def check_rules(self) -> "SearchRequest":
        if self.origin == self.destination:
            raise ValueError("origin and destination must differ")
        if self.depart_date < date.today():
            raise ValueError("departDate must be today or later")
        if self.trip_type == "roundtrip":
            if self.return_date is None:
                raise ValueError("returnDate is required for roundtrip")
            if self.return_date < self.depart_date:
                raise ValueError("returnDate cannot be before departDate")
        else:
            self.return_date = None
        return self


class Airport(CamelModel):
    iata: str
    name: str
    city: str
    country: str


class AirportInfo(CamelModel):
    city: str
    name: str
    country: str


class Price(CamelModel):
    total: float
    base: float
    taxes: float
    currency: str
    per_adult: float


class Baggage(CamelModel):
    checked: str | None = None


class Segment(CamelModel):
    from_: IataCode = Field(validation_alias="from", serialization_alias="from")
    to: IataCode
    depart_at: LocalDateTime
    arrive_at: LocalDateTime
    duration_minutes: int
    marketing_carrier: str
    operating_carrier: str
    flight_number: str
    aircraft: str | None = None
    booking_class: str | None = None
    cabin: Cabin
    departure_terminal: str | None = None
    arrival_terminal: str | None = None
    layover_minutes: int | None = None


class Leg(CamelModel):
    id: str
    from_: IataCode = Field(validation_alias="from", serialization_alias="from")
    to: IataCode
    depart_at: LocalDateTime
    arrive_at: LocalDateTime
    duration_minutes: int
    stops: int
    carriers: list[str]
    segments: list[Segment] = Field(min_length=1)


class Itinerary(CamelModel):
    id: str
    price: Price
    validating_carrier: str
    refundable: bool
    seats_left: int | None = None
    cabin: Cabin
    baggage: Baggage
    legs: list[Leg] = Field(min_length=1, max_length=2)


class SearchMeta(CamelModel):
    count: int
    provider: Literal["sabre", "mock"]
    fetched_at: UtcDateTime


class SearchResponse(CamelModel):
    search_id: str
    query: SearchRequest
    currency: str
    itineraries: list[Itinerary]
    airlines: dict[str, str]
    airports: dict[str, AirportInfo]
    meta: SearchMeta


class FareBreakdownItem(CamelModel):
    passenger_type: PassengerType
    count: int
    base: float
    taxes: float
    total: float


class TaxItem(CamelModel):
    code: str
    amount: float
    description: str


class ItineraryDetailFields(CamelModel):
    fare_breakdown: list[FareBreakdownItem]
    taxes: list[TaxItem]
    last_ticket_date: date | None = None
    fare_basis: list[str]


class ItineraryDetail(Itinerary, ItineraryDetailFields):
    search_id: str
    query: SearchRequest
    airlines: dict[str, str]
    airports: dict[str, AirportInfo]
    notes: list[str]


class HealthResponse(CamelModel):
    status: Literal["ok"]
    provider: Literal["sabre", "mock"]


class ErrorDetail(CamelModel):
    code: str
    message: str


class ErrorBody(CamelModel):
    error: ErrorDetail
