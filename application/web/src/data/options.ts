import type { Cabin, PassengerType, TripType } from '../api/types'

export const TRIP_TYPES: { value: TripType; label: string }[] = [
  { value: 'roundtrip', label: 'Round trip' },
  { value: 'oneway', label: 'One way' },
]

export const CABINS: { value: Cabin; label: string }[] = [
  { value: 'economy', label: 'Economy' },
  { value: 'premium_economy', label: 'Premium economy' },
  { value: 'business', label: 'Business' },
  { value: 'first', label: 'First' },
]

export const CABIN_LABELS: Record<Cabin, string> = Object.fromEntries(
  CABINS.map((c) => [c.value, c.label]),
) as Record<Cabin, string>

export const PASSENGER_LABELS: Record<PassengerType, string> = {
  adult: 'Adult',
  child: 'Child',
  infant: 'Infant',
}
