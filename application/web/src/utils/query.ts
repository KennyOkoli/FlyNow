import type { LocationQuery, LocationQueryRaw, LocationQueryValue } from 'vue-router'
import type { Cabin, SearchRequest, TripType } from '../api/types'

const IATA = /^[A-Z]{3}$/
const YMD = /^\d{4}-\d{2}-\d{2}$/
const TRIP_TYPES: TripType[] = ['oneway', 'roundtrip']
const CABINS: Cabin[] = ['economy', 'premium_economy', 'business', 'first']

export function toQuery(req: SearchRequest): LocationQueryRaw {
  const q: Record<string, string> = {
    tripType: req.tripType,
    origin: req.origin,
    destination: req.destination,
    departDate: req.departDate,
    adults: String(req.passengers.adults),
    children: String(req.passengers.children),
    infants: String(req.passengers.infants),
    cabin: req.cabin,
  }
  if (req.tripType === 'roundtrip' && req.returnDate) q.returnDate = req.returnDate
  if (req.currency) q.currency = req.currency
  return q
}

function first(v: LocationQueryValue | LocationQueryValue[] | undefined): string | undefined {
  const value = Array.isArray(v) ? v[0] : v
  return typeof value === 'string' ? value : undefined
}

function int(v: string | undefined, fallback: number): number {
  if (v === undefined || v === '') return fallback
  const n = Number(v)
  return Number.isInteger(n) ? n : NaN
}

export function fromQuery(q: LocationQuery): SearchRequest | null {
  const tripType = first(q.tripType) as TripType | undefined
  const origin = first(q.origin)?.toUpperCase()
  const destination = first(q.destination)?.toUpperCase()
  const departDate = first(q.departDate)
  const returnDate = first(q.returnDate)
  const cabin = (first(q.cabin) ?? 'economy') as Cabin
  const adults = int(first(q.adults), 1)
  const children = int(first(q.children), 0)
  const infants = int(first(q.infants), 0)
  const currency = first(q.currency)

  if (!tripType || !TRIP_TYPES.includes(tripType)) return null
  if (!origin || !destination || !IATA.test(origin) || !IATA.test(destination) || origin === destination) return null
  if (!departDate || !YMD.test(departDate)) return null
  if (tripType === 'roundtrip' && (!returnDate || !YMD.test(returnDate) || returnDate < departDate)) return null
  if (!CABINS.includes(cabin)) return null
  if (adults < 1 || adults > 9 || children < 0 || children > 8 || infants < 0 || infants > adults) return null
  if (adults + children + infants > 9) return null

  const req: SearchRequest = {
    tripType,
    origin,
    destination,
    departDate,
    passengers: { adults, children, infants },
    cabin,
  }
  if (tripType === 'roundtrip' && returnDate) req.returnDate = returnDate
  if (currency && /^[A-Z]{3}$/.test(currency)) req.currency = currency
  return req
}
