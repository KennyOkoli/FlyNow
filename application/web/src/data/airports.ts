import type { Airport } from '../api/types'

export const AIRPORTS: Record<string, Airport> = {
  LOS: { iata: 'LOS', city: 'Lagos', name: 'Murtala Muhammed International Airport', country: 'Nigeria' },
  ABV: { iata: 'ABV', city: 'Abuja', name: 'Nnamdi Azikiwe International Airport', country: 'Nigeria' },
  PHC: { iata: 'PHC', city: 'Port Harcourt', name: 'Port Harcourt International Airport', country: 'Nigeria' },
  LHR: { iata: 'LHR', city: 'London', name: 'Heathrow Airport', country: 'United Kingdom' },
  DXB: { iata: 'DXB', city: 'Dubai', name: 'Dubai International Airport', country: 'United Arab Emirates' },
  JFK: { iata: 'JFK', city: 'New York', name: 'John F. Kennedy International Airport', country: 'United States' },
  ACC: { iata: 'ACC', city: 'Accra', name: 'Kotoka International Airport', country: 'Ghana' },
  JNB: { iata: 'JNB', city: 'Johannesburg', name: 'O. R. Tambo International Airport', country: 'South Africa' },
  CDG: { iata: 'CDG', city: 'Paris', name: 'Charles de Gaulle Airport', country: 'France' },
  YYZ: { iata: 'YYZ', city: 'Toronto', name: 'Toronto Pearson International Airport', country: 'Canada' },
  IST: { iata: 'IST', city: 'Istanbul', name: 'Istanbul Airport', country: 'Turkey' },
  NBO: { iata: 'NBO', city: 'Nairobi', name: 'Jomo Kenyatta International Airport', country: 'Kenya' },
  CPT: { iata: 'CPT', city: 'Cape Town', name: 'Cape Town International Airport', country: 'South Africa' },
}

export interface PopularRoute {
  from: string
  to: string
  note: string
}

export const POPULAR_ROUTES: PopularRoute[] = [
  { from: 'LOS', to: 'LHR', note: 'Nonstop in about 6h 40m' },
  { from: 'LOS', to: 'DXB', note: 'Nonstop in about 7h 30m' },
  { from: 'ABV', to: 'LOS', note: 'Domestic, about 1h 15m' },
  { from: 'LOS', to: 'JFK', note: 'Nonstop in about 11h 30m' },
  { from: 'PHC', to: 'LOS', note: 'Domestic, about 1h 10m' },
  { from: 'LOS', to: 'ACC', note: 'Nonstop in about 1h 10m' },
]
