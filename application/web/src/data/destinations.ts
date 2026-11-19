import credits from './destination-credits.json'

export interface Destination {
  iata: string
  city: string
  country: string
  blurb: string
  image: string
  credit: { artist: string; license: string; source: string }
}

const LIST: Omit<Destination, 'image' | 'credit'>[] = [
  { iata: 'LHR', city: 'London', country: 'United Kingdom', blurb: 'Family, school runs and the West End' },
  { iata: 'DXB', city: 'Dubai', country: 'UAE', blurb: 'Shopping, sun and easy connections' },
  { iata: 'JFK', city: 'New York', country: 'United States', blurb: 'The city that never sleeps' },
  { iata: 'ACC', city: 'Accra', country: 'Ghana', blurb: 'A short hop for a long weekend' },
  { iata: 'NBO', city: 'Nairobi', country: 'Kenya', blurb: 'Safari on the edge of the city' },
  { iata: 'CPT', city: 'Cape Town', country: 'South Africa', blurb: 'Table Mountain and the coast' },
  { iata: 'IST', city: 'Istanbul', country: 'Turkey', blurb: 'Where two continents meet' },
  { iata: 'CDG', city: 'Paris', country: 'France', blurb: 'Evenings along the Seine' },
  { iata: 'YYZ', city: 'Toronto', country: 'Canada', blurb: 'A new chapter for many' },
  { iata: 'JNB', city: 'Johannesburg', country: 'South Africa', blurb: 'Business hub of the south' },
]

const CREDITS = credits as Record<string, Destination['credit']>

export const DESTINATIONS: Destination[] = LIST.map((d) => ({
  ...d,
  image: `/destinations/${d.iata.toLowerCase()}.jpg`,
  credit: CREDITS[d.iata] ?? { artist: '', license: '', source: '' },
}))
