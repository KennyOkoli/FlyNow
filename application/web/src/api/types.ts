export type TripType = 'oneway' | 'roundtrip'
export type Cabin = 'economy' | 'premium_economy' | 'business' | 'first'
export type PassengerType = 'adult' | 'child' | 'infant'
export type Provider = 'sabre' | 'mock'

export type ApiErrorCode =
  | 'validation_error'
  | 'not_found'
  | 'search_expired'
  | 'provider_error'
  | 'provider_auth_error'

export interface ApiErrorBody {
  error: { code: ApiErrorCode | string; message: string }
}

export interface HealthResponse {
  status: 'ok'
  provider: Provider
}

export interface Airport {
  iata: string
  name: string
  city: string
  country: string
}

export type AirportInfo = Omit<Airport, 'iata'>

export interface Passengers {
  adults: number
  children: number
  infants: number
}

export interface SearchRequest {
  tripType: TripType
  origin: string
  destination: string
  departDate: string
  returnDate?: string
  passengers: Passengers
  cabin: Cabin
  currency?: string
}

export interface Price {
  total: number
  base: number
  taxes: number
  currency: string
  perAdult: number
}

export interface Baggage {
  checked: string | null
}

export interface Segment {
  from: string
  to: string
  departAt: string
  arriveAt: string
  durationMinutes: number
  marketingCarrier: string
  operatingCarrier: string
  flightNumber: string
  aircraft: string
  bookingClass: string
  cabin: Cabin
  departureTerminal: string | null
  arrivalTerminal: string | null
  layoverMinutes: number | null
}

export interface Leg {
  id: string
  from: string
  to: string
  departAt: string
  arriveAt: string
  durationMinutes: number
  stops: number
  carriers: string[]
  segments: Segment[]
}

export interface Itinerary {
  id: string
  price: Price
  validatingCarrier: string
  refundable: boolean
  seatsLeft: number | null
  cabin: Cabin
  baggage: Baggage
  legs: Leg[]
}

export interface SearchMeta {
  count: number
  provider: Provider
  fetchedAt: string
}

export interface SearchResponse {
  searchId: string
  query: SearchRequest
  currency: string
  itineraries: Itinerary[]
  airlines: Record<string, string>
  airports: Record<string, AirportInfo>
  meta: SearchMeta
}

export interface FareBreakdownRow {
  passengerType: PassengerType
  count: number
  base: number
  taxes: number
  total: number
}

export interface TaxLine {
  code: string
  amount: number
  description: string
}

export interface ItineraryDetail extends Itinerary {
  searchId: string
  query: SearchRequest
  airlines: Record<string, string>
  airports: Record<string, AirportInfo>
  fareBreakdown: FareBreakdownRow[]
  taxes: TaxLine[]
  lastTicketDate: string
  fareBasis: string[]
  notes: string[]
}
