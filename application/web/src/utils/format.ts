import type { Passengers } from '../api/types'

export interface IsoParts {
  year: number
  month: number
  day: number
  hour: number
  minute: number
}

const ISO = /^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2}))?/

export function isoParts(iso: string): IsoParts | null {
  const m = ISO.exec(iso)
  if (!m) return null
  return {
    year: Number(m[1]),
    month: Number(m[2]),
    day: Number(m[3]),
    hour: m[4] ? Number(m[4]) : 0,
    minute: m[5] ? Number(m[5]) : 0,
  }
}

const pad = (n: number) => String(n).padStart(2, '0')
const utcDate = (p: IsoParts) => new Date(Date.UTC(p.year, p.month - 1, p.day))

export function formatTime(iso: string): string {
  const p = isoParts(iso)
  return p ? `${pad(p.hour)}:${pad(p.minute)}` : ''
}

export function formatDate(iso: string, style: 'short' | 'medium' | 'long' = 'short'): string {
  const p = isoParts(iso)
  if (!p) return ''
  const options: Intl.DateTimeFormatOptions =
    style === 'long'
      ? { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }
      : style === 'medium'
        ? { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' }
        : { weekday: 'short', day: 'numeric', month: 'short', timeZone: 'UTC' }
  return new Intl.DateTimeFormat('en-GB', options).format(utcDate(p))
}

export function formatDuration(minutes: number): string {
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  if (h === 0) return `${m}m`
  if (m === 0) return `${h}h`
  return `${h}h ${m}m`
}

export function formatMoney(amount: number, currency: string): string {
  try {
    return new Intl.NumberFormat('en', { style: 'currency', currency, maximumFractionDigits: 2 }).format(amount)
  } catch {
    return `${currency} ${amount.toFixed(2)}`
  }
}

export function dayOffset(departAt: string, arriveAt: string): number {
  const a = isoParts(departAt)
  const b = isoParts(arriveAt)
  if (!a || !b) return 0
  return Math.round((utcDate(b).getTime() - utcDate(a).getTime()) / 86_400_000)
}

export type TimeBucket = 'morning' | 'afternoon' | 'evening' | 'night'

export const TIME_BUCKETS: { id: TimeBucket; label: string; range: string }[] = [
  { id: 'morning', label: 'Morning', range: '05:00 to 11:59' },
  { id: 'afternoon', label: 'Afternoon', range: '12:00 to 16:59' },
  { id: 'evening', label: 'Evening', range: '17:00 to 20:59' },
  { id: 'night', label: 'Night', range: '21:00 to 04:59' },
]

export function timeBucket(iso: string): TimeBucket {
  const h = isoParts(iso)?.hour ?? 0
  if (h >= 5 && h < 12) return 'morning'
  if (h >= 12 && h < 17) return 'afternoon'
  if (h >= 17 && h < 21) return 'evening'
  return 'night'
}

function plural(count: number, one: string, many = `${one}s`): string {
  return `${count} ${count === 1 ? one : many}`
}

export function formatPassengers(p: Passengers): string {
  const parts = [plural(p.adults, 'adult')]
  if (p.children > 0) parts.push(plural(p.children, 'child', 'children'))
  if (p.infants > 0) parts.push(plural(p.infants, 'infant'))
  return parts.join(', ')
}

export function totalPassengers(p: Passengers): number {
  return p.adults + p.children + p.infants
}

export function todayYmd(): string {
  const d = new Date()
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

export function addDays(ymd: string, days: number): string {
  const p = isoParts(ymd)
  if (!p) return ymd
  const d = utcDate(p)
  d.setUTCDate(d.getUTCDate() + days)
  return `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())}`
}
