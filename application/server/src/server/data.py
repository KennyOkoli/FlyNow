import json
from functools import lru_cache
from pathlib import Path
from typing import TypedDict

from server.schemas import AirportInfo

DATA_DIR = Path(__file__).parent / "data"

AIRLINE_OVERRIDES: dict[str, str] = {
    "W3": "Arik Air",
    "P4": "Air Peace",
    "Q9": "Green Africa",
    "9J": "Dana Air",
    "VL": "Med-View Airline",
    "LH": "Lufthansa",
    "KQ": "Kenya Airways",
    "AT": "Royal Air Maroc",
    "MS": "EgyptAir",
    "ET": "Ethiopian Airlines",
    "BA": "British Airways",
    "TK": "Turkish Airlines",
    "QR": "Qatar Airways",
    "EK": "Emirates",
    "AF": "Air France",
    "KL": "KLM",
    "VS": "Virgin Atlantic",
    "DL": "Delta Air Lines",
    "UA": "United Airlines",
    "AA": "American Airlines",
    "SA": "South African Airways",
    "WB": "RwandAir",
    "HF": "Air Côte d'Ivoire",
    "AW": "Africa World Airlines",
    "KP": "ASKY Airlines",
    "GF": "Gulf Air",
    "HR": "Hahn Air Lines",
    "H1": "Hahn Air Systems",
    "X1": "Hahn Air Technologies",
    "UN": "United Nigeria Airlines",
}


class _AirportRequired(TypedDict):
    iata: str
    name: str
    city: str
    country: str


class AirportRecord(_AirportRequired, total=False):
    tz: str
    lat: float
    lon: float


@lru_cache
def load_airports() -> list[AirportRecord]:
    with (DATA_DIR / "airports.json").open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache
def airports_by_iata() -> dict[str, AirportRecord]:
    return {a["iata"]: a for a in load_airports()}


@lru_cache
def load_airlines() -> dict[str, str]:
    with (DATA_DIR / "airlines.json").open(encoding="utf-8") as f:
        names: dict[str, str] = json.load(f)
    names.update(AIRLINE_OVERRIDES)
    return names


def airline_name(code: str) -> str:
    return load_airlines().get(code, code)


def airport_info(code: str) -> AirportInfo:
    record = airports_by_iata().get(code)
    if record is None:
        return AirportInfo(city=code, name=code, country="")
    return AirportInfo(city=record["city"], name=record["name"], country=record["country"])


def airlines_map(codes: set[str]) -> dict[str, str]:
    return {code: airline_name(code) for code in sorted(codes)}


def airports_map(codes: set[str]) -> dict[str, AirportInfo]:
    return {code: airport_info(code) for code in sorted(codes)}
