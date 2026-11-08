from fastapi import APIRouter, Query

from server.data import load_airports
from server.schemas import Airport

router = APIRouter(prefix="/airports", tags=["airports"])

MAX_LIMIT = 20
# Tie-break within a match tier so big hubs beat small fields that share a prefix (Lagos vs Laghouat).
MAJOR_AIRPORTS = frozenset(
    "LOS ABV PHC KAN ENU ACC ABJ DKR NBO ADD JNB CPT CAI CMN KGL EBB DAR LHR LGW MAN DUB CDG AMS FRA MUC ZRH VIE "
    "FCO MAD BCN LIS BRU IST DOH DXB AUH JED RUH JFK EWR IAD ATL ORD LAX SFO MIA DFW BOS IAH SEA YYZ YUL DEL BOM "
    "DAC BKK SIN KUL HKG NRT HND ICN PEK PVG SYD MEL GRU EZE MEX".split()
)


def _rank(term: str, iata: str, city: str, name: str) -> int | None:
    if iata == term:
        return 0
    if iata.startswith(term):
        return 1
    if city.startswith(term):
        return 2
    if name.startswith(term):
        return 3
    if term in city:
        return 4
    if term in name:
        return 5
    return None


@router.get("", response_model=list[Airport])
async def search_airports(q: str = Query(default=""), limit: int = Query(default=8, ge=1)) -> list[Airport]:
    term = q.strip().lower()
    if not term:
        return []
    limit = min(limit, MAX_LIMIT)
    ranked: list[tuple[tuple[int, int, int, int], Airport]] = []
    for index, record in enumerate(load_airports()):
        rank = _rank(term, record["iata"].lower(), record["city"].lower(), record["name"].lower())
        if rank is not None:
            key = (rank, 0 if record["iata"] in MAJOR_AIRPORTS else 1, len(record["city"]), index)
            ranked.append((key, Airport(**{k: record[k] for k in ("iata", "name", "city", "country")})))
    ranked.sort(key=lambda item: item[0])
    return [airport for _, airport in ranked[:limit]]
