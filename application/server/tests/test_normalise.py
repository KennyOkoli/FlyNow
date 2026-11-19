import json
from datetime import datetime
from pathlib import Path

import pytest

from server.normalise import normalise
from server.providers.base import SearchResult
from server.schemas import Itinerary

SAMPLE = Path(__file__).resolve().parents[1] / "src" / "server" / "data" / "sabre_bfm_sample_response.json"


@pytest.fixture(scope="module")
def result() -> SearchResult:
    gir = json.loads(SAMPLE.read_text(encoding="utf-8"))["groupedItineraryResponse"]
    return normalise(gir, {"adult": 1, "child": 0, "infant": 0})


def _aware(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    assert parsed.tzinfo is not None, value
    return parsed


def test_sample_yields_48_roundtrip_itineraries(result: SearchResult) -> None:
    assert len(result.itineraries) == 48
    assert all(len(it.legs) == 2 for it in result.itineraries)
    assert [it.id for it in result.itineraries] == [f"it_{n}" for n in range(1, 49)]
    leg_ids = [leg.id for it in result.itineraries for leg in it.legs]
    assert len(set(leg_ids)) == len(leg_ids)


def test_every_itinerary_validates_as_contract_json(result: SearchResult) -> None:
    for itinerary in result.itineraries:
        payload = json.loads(itinerary.model_dump_json())
        Itinerary.model_validate(payload)
        assert payload["price"]["total"] > 0
        assert payload["price"]["currency"] == "BDT"
        for leg in payload["legs"]:
            depart, arrive = _aware(leg["departAt"]), _aware(leg["arriveAt"])
            assert arrive > depart
            assert leg["durationMinutes"] > 0
            assert leg["stops"] == len(leg["segments"]) - 1
            for index, segment in enumerate(leg["segments"]):
                seg_depart, seg_arrive = _aware(segment["departAt"]), _aware(segment["arriveAt"])
                assert seg_arrive > seg_depart
                assert segment["durationMinutes"] > 0
                if index == 0:
                    assert segment["layoverMinutes"] is None
                else:
                    assert segment["layoverMinutes"] >= 0


def test_date_adjustments_shift_calendar_days(result: SearchResult) -> None:
    # Schedule 13 is BOM 22:45 -> DEL 00:55 with arrival dateAdjustment 1.
    overnight = [
        seg
        for it in result.itineraries
        for leg in it.legs
        for seg in leg.segments
        if seg.from_ == "BOM" and seg.to == "DEL" and seg.depart_at.strftime("%H:%M") == "22:45"
    ]
    assert overnight, "expected the 22:45 BOM-DEL segment in the sample"
    for seg in overnight:
        assert seg.arrive_at.date() > seg.depart_at.date()
        assert seg.duration_minutes > 0


def test_offsets_are_preserved_not_converted(result: SearchResult) -> None:
    first = result.itineraries[0].legs[0].segments[0]
    assert first.from_ == "DAC"
    assert first.depart_at.isoformat().endswith("+06:00")
    assert first.arrive_at.isoformat().endswith("+07:00")


def test_detail_fields_resolved_from_descs(result: SearchResult) -> None:
    detail = result.details["it_1"]
    assert detail.fare_breakdown[0].passenger_type == "adult"
    assert detail.fare_breakdown[0].count == 1
    assert detail.fare_breakdown[0].total == result.itineraries[0].price.total
    assert detail.taxes and all(t.code and t.amount >= 0 for t in detail.taxes)
    assert detail.fare_basis == ["BBD1M"]
    assert detail.last_ticket_date is not None
    first = result.itineraries[0]
    assert first.validating_carrier == "BG"
    assert first.baggage.checked == "30 kg"
    assert first.seats_left == 9
    assert first.refundable is True
    assert first.legs[0].segments[0].flight_number == "BG388"
    assert first.legs[0].segments[0].booking_class == "B"
    assert first.price.base + first.price.taxes == pytest.approx(first.price.total)


def test_reference_sets_cover_everything(result: SearchResult) -> None:
    carriers = {s.marketing_carrier for it in result.itineraries for leg in it.legs for s in leg.segments}
    airports = {a for it in result.itineraries for leg in it.legs for s in leg.segments for a in (s.from_, s.to)}
    assert carriers <= result.airline_codes
    assert airports == result.airport_codes
    assert {it.validating_carrier for it in result.itineraries} <= result.airline_codes
