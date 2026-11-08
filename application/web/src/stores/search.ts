import { defineStore } from 'pinia'
import { ref } from 'vue'
import { ApiError, searchFlights } from '../api/client'
import type { Airport, AirportInfo, SearchRequest, SearchResponse } from '../api/types'

const CACHE_TTL_MS = 30 * 60 * 1000

export function queryKey(q: SearchRequest): string {
  return [
    q.tripType,
    q.origin,
    q.destination,
    q.departDate,
    q.tripType === 'roundtrip' ? (q.returnDate ?? '') : '',
    q.passengers.adults,
    q.passengers.children,
    q.passengers.infants,
    q.cabin,
    q.currency ?? 'USD',
  ].join('|')
}

export const useSearchStore = defineStore('search', () => {
  const lastQuery = ref<SearchRequest | null>(null)
  const knownAirports = ref<Record<string, Airport>>({})
  const results = ref<Record<string, SearchResponse>>({})
  const searchIdByKey = ref<Record<string, string>>({})
  const fetchedAt = ref<Record<string, number>>({})
  const loading = ref(false)
  const error = ref<ApiError | null>(null)

  function setLastQuery(q: SearchRequest) {
    lastQuery.value = q
  }

  function rememberAirports(list: Airport[]) {
    for (const a of list) knownAirports.value[a.iata] = a
  }

  function rememberAirportMap(map: Record<string, AirportInfo>) {
    for (const [iata, info] of Object.entries(map)) knownAirports.value[iata] = { iata, ...info }
  }

  function getResults(searchId: string): SearchResponse | undefined {
    return results.value[searchId]
  }

  function cachedFor(q: SearchRequest): SearchResponse | undefined {
    const id = searchIdByKey.value[queryKey(q)]
    if (!id) return undefined
    const at = fetchedAt.value[id] ?? 0
    if (Date.now() - at > CACHE_TTL_MS) return undefined
    return results.value[id]
  }

  async function search(q: SearchRequest, options: { force?: boolean } = {}): Promise<SearchResponse> {
    setLastQuery(q)
    const cached = options.force ? undefined : cachedFor(q)
    if (cached) return cached

    loading.value = true
    error.value = null
    try {
      const res = await searchFlights(q)
      results.value[res.searchId] = res
      searchIdByKey.value[queryKey(q)] = res.searchId
      fetchedAt.value[res.searchId] = Date.now()
      rememberAirportMap(res.airports)
      return res
    } catch (e) {
      error.value = e instanceof ApiError ? e : new ApiError(0, 'unknown', 'Something went wrong while searching.')
      throw error.value
    } finally {
      loading.value = false
    }
  }

  return {
    lastQuery,
    knownAirports,
    results,
    loading,
    error,
    setLastQuery,
    rememberAirports,
    rememberAirportMap,
    getResults,
    cachedFor,
    search,
  }
})
