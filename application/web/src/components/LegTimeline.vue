<script setup lang="ts">
import type { AirportInfo, Leg } from '../api/types'
import { CABIN_LABELS } from '../data/options'
import { dayOffset, formatDate, formatDuration, formatTime } from '../utils/format'
import AirlineLogo from './AirlineLogo.vue'

const props = defineProps<{
  leg: Leg
  title: string
  airlines: Record<string, string>
  airports: Record<string, AirportInfo>
}>()

function place(code: string): string {
  const a = props.airports[code]
  return a ? `${a.city} (${code})` : code
}
</script>

<template>
  <section class="card p-4 sm:p-6" :aria-label="title">
    <header class="flex flex-wrap items-baseline justify-between gap-2">
      <h2 class="text-lg font-semibold">{{ title }}: {{ place(leg.from) }} to {{ place(leg.to) }}</h2>
      <p class="text-sm text-ink-2">
        {{ formatDate(leg.departAt, 'medium') }} · {{ formatDuration(leg.durationMinutes) }} ·
        {{ leg.stops === 0 ? 'Nonstop' : `${leg.stops} stop${leg.stops > 1 ? 's' : ''}` }}
      </p>
    </header>

    <ol class="mt-5">
      <li v-for="(seg, i) in leg.segments" :key="`${seg.flightNumber}-${i}`">
        <div
          v-if="seg.layoverMinutes !== null"
          class="my-3 ml-[19px] flex items-center gap-3 border-l-2 border-dashed border-amber/50 py-2 pl-6 text-sm"
        >
          <span class="tag tag-amber">Layover</span>
          <span class="text-ink-2">{{ place(seg.from) }} · {{ formatDuration(seg.layoverMinutes) }}</span>
        </div>

        <div class="grid grid-cols-[40px_1fr] gap-x-3">
          <div class="flex flex-col items-center">
            <span class="mt-1.5 h-3 w-3 rounded-full border-2 border-cobalt bg-surface" aria-hidden="true" />
            <span class="my-1 w-px flex-1 bg-line-strong" aria-hidden="true" />
            <span class="mb-1.5 h-3 w-3 rounded-full bg-cobalt" aria-hidden="true" />
          </div>

          <div class="flex flex-col gap-3">
            <div>
              <p class="tabular font-semibold">
                {{ formatTime(seg.departAt) }}
                <span class="font-normal text-ink-2">· {{ formatDate(seg.departAt) }}</span>
              </p>
              <p class="text-sm text-ink-2">
                {{ airports[seg.from]?.name ?? seg.from }} ({{ seg.from }})<span v-if="seg.departureTerminal">, Terminal {{ seg.departureTerminal }}</span>
              </p>
            </div>

            <div class="flex items-center gap-3 rounded-[10px] bg-paper p-3 text-sm">
              <AirlineLogo :code="seg.marketingCarrier" :name="airlines[seg.marketingCarrier]" size="sm" />
              <div class="min-w-0">
                <p class="font-semibold">{{ airlines[seg.marketingCarrier] ?? seg.marketingCarrier }} · {{ seg.flightNumber }}</p>
                <p class="text-xs text-ink-2">
                  {{ CABIN_LABELS[seg.cabin] }} ({{ seg.bookingClass }}) · Aircraft {{ seg.aircraft }} ·
                  {{ formatDuration(seg.durationMinutes) }}
                  <template v-if="seg.operatingCarrier !== seg.marketingCarrier">
                    · Operated by {{ airlines[seg.operatingCarrier] ?? seg.operatingCarrier }}
                  </template>
                </p>
              </div>
            </div>

            <div>
              <p class="tabular font-semibold">
                {{ formatTime(seg.arriveAt) }}
                <span class="font-normal text-ink-2">· {{ formatDate(seg.arriveAt) }}</span>
                <span v-if="dayOffset(seg.departAt, seg.arriveAt) > 0" class="tag tag-amber ml-1">Next day</span>
              </p>
              <p class="text-sm text-ink-2">
                {{ airports[seg.to]?.name ?? seg.to }} ({{ seg.to }})<span v-if="seg.arrivalTerminal">, Terminal {{ seg.arrivalTerminal }}</span>
              </p>
            </div>
          </div>
        </div>
      </li>
    </ol>
  </section>
</template>
