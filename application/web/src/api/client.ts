import type { Airport, ApiErrorBody, ItineraryDetail, SearchRequest, SearchResponse } from './types'

export class ApiError extends Error {
  readonly status: number
  readonly code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

function isAbort(e: unknown): boolean {
  return e instanceof DOMException && e.name === 'AbortError'
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let res: Response
  try {
    res = await fetch(path, {
      ...init,
      headers: { Accept: 'application/json', ...(init.body ? { 'Content-Type': 'application/json' } : {}), ...init.headers },
    })
  } catch (e) {
    if (isAbort(e)) throw e
    throw new ApiError(0, 'network_error', 'Could not reach the server. Check your connection and try again.')
  }

  if (!res.ok) {
    let code = 'http_error'
    let message = res.statusText || `Request failed with status ${res.status}`
    try {
      const body = (await res.json()) as Partial<ApiErrorBody>
      if (body.error?.code) code = body.error.code
      if (body.error?.message) message = body.error.message
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, code, message)
  }

  return (await res.json()) as T
}

export function searchAirports(q: string, limit = 8, signal?: AbortSignal): Promise<Airport[]> {
  const params = new URLSearchParams({ q, limit: String(limit) })
  return request<Airport[]>(`/api/airports?${params}`, { signal })
}

export function searchFlights(body: SearchRequest, signal?: AbortSignal): Promise<SearchResponse> {
  return request<SearchResponse>('/api/flights/search', { method: 'POST', body: JSON.stringify(body), signal })
}

export function getItinerary(searchId: string, itineraryId: string, signal?: AbortSignal): Promise<ItineraryDetail> {
  return request<ItineraryDetail>(
    `/api/flights/${encodeURIComponent(searchId)}/itineraries/${encodeURIComponent(itineraryId)}`,
    { signal },
  )
}
