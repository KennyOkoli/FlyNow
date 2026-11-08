import type { Itinerary } from '../api/types'
import { timeBucket, type TimeBucket } from './format'

export type StopFilter = '0' | '1' | '2+'
export type SortKey = 'cheapest' | 'fastest' | 'earliest'

export interface Filters {
  stops: StopFilter[]
  airlines: string[]
  priceMin: number | null
  priceMax: number | null
  departBuckets: TimeBucket[]
  maxDuration: number | null
}

export interface FilterOptions {
  airlines: { code: string; name: string; count: number }[]
  stopCounts: Record<StopFilter, number>
  priceMin: number
  priceMax: number
  durationMin: number
  durationMax: number
  currency: string
}

export const STOP_FILTERS: { id: StopFilter; label: string }[] = [
  { id: '0', label: 'Nonstop' },
  { id: '1', label: '1 stop' },
  { id: '2+', label: '2 or more stops' },
]

export const SORT_KEYS: { id: SortKey; label: string }[] = [
  { id: 'cheapest', label: 'Cheapest' },
  { id: 'fastest', label: 'Fastest' },
  { id: 'earliest', label: 'Earliest departure' },
]

export const emptyFilters = (): Filters => ({
  stops: [],
  airlines: [],
  priceMin: null,
  priceMax: null,
  departBuckets: [],
  maxDuration: null,
})

export function activeFilterCount(f: Filters): number {
  let n = 0
  if (f.stops.length) n++
  if (f.airlines.length) n++
  if (f.priceMin !== null || f.priceMax !== null) n++
  if (f.departBuckets.length) n++
  if (f.maxDuration !== null) n++
  return n
}

export function itineraryStops(it: Itinerary): number {
  return it.legs.reduce((max, leg) => Math.max(max, leg.stops), 0)
}

export function stopFilterOf(it: Itinerary): StopFilter {
  const s = itineraryStops(it)
  return s === 0 ? '0' : s === 1 ? '1' : '2+'
}

export function itineraryDuration(it: Itinerary): number {
  return it.legs.reduce((sum, leg) => sum + leg.durationMinutes, 0)
}

export function itineraryCarriers(it: Itinerary): string[] {
  const set = new Set<string>([it.validatingCarrier])
  for (const leg of it.legs) for (const c of leg.carriers) set.add(c)
  return [...set]
}

function firstDeparture(it: Itinerary): string {
  return it.legs[0]?.departAt ?? ''
}

export function buildFilterOptions(
  its: Itinerary[],
  airlineNames: Record<string, string>,
  currency: string,
): FilterOptions {
  const airlineCounts = new Map<string, number>()
  const stopCounts: Record<StopFilter, number> = { '0': 0, '1': 0, '2+': 0 }
  let priceMin = Infinity
  let priceMax = 0
  let durationMin = Infinity
  let durationMax = 0

  for (const it of its) {
    for (const c of itineraryCarriers(it)) airlineCounts.set(c, (airlineCounts.get(c) ?? 0) + 1)
    stopCounts[stopFilterOf(it)]++
    priceMin = Math.min(priceMin, it.price.total)
    priceMax = Math.max(priceMax, it.price.total)
    const d = itineraryDuration(it)
    durationMin = Math.min(durationMin, d)
    durationMax = Math.max(durationMax, d)
  }

  const airlines = [...airlineCounts.entries()]
    .map(([code, count]) => ({ code, name: airlineNames[code] ?? code, count }))
    .sort((a, b) => a.name.localeCompare(b.name))

  return {
    airlines,
    stopCounts,
    priceMin: its.length ? Math.floor(priceMin) : 0,
    priceMax: its.length ? Math.ceil(priceMax) : 0,
    durationMin: its.length ? durationMin : 0,
    durationMax: its.length ? durationMax : 0,
    currency,
  }
}

export function applyFilters(its: Itinerary[], f: Filters): Itinerary[] {
  return its.filter((it) => {
    if (f.stops.length && !f.stops.includes(stopFilterOf(it))) return false
    if (f.airlines.length && !itineraryCarriers(it).some((c) => f.airlines.includes(c))) return false
    if (f.priceMin !== null && it.price.total < f.priceMin) return false
    if (f.priceMax !== null && it.price.total > f.priceMax) return false
    if (f.departBuckets.length && !f.departBuckets.includes(timeBucket(firstDeparture(it)))) return false
    if (f.maxDuration !== null && itineraryDuration(it) > f.maxDuration) return false
    return true
  })
}

export function sortItineraries(its: Itinerary[], key: SortKey): Itinerary[] {
  const sorted = [...its]
  switch (key) {
    case 'cheapest':
      return sorted.sort((a, b) => a.price.total - b.price.total)
    case 'fastest':
      return sorted.sort((a, b) => itineraryDuration(a) - itineraryDuration(b))
    case 'earliest':
      return sorted.sort((a, b) => firstDeparture(a).slice(0, 16).localeCompare(firstDeparture(b).slice(0, 16)))
  }
}
