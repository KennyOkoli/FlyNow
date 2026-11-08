<script setup lang="ts">
import { computed } from 'vue'
import type { AirportInfo, Itinerary, Leg } from '../api/types'
import { dayOffset, formatDuration, formatMoney, formatTime } from '../utils/format'
import AirlineLogo from './AirlineLogo.vue'

const props = defineProps<{
  itinerary: Itinerary
  searchId: string
  airlines: Record<string, string>
  airports: Record<string, AirportInfo>
}>()

const legLabels = computed(() => (props.itinerary.legs.length > 1 ? ['Outbound', 'Return'] : ['']))

function airlineName(code: string): string {
  return props.airlines[code] ?? code
}

function stopsText(leg: Leg): string {
  if (leg.stops === 0) return 'Nonstop'
  const layovers = leg.segments
    .slice(1)
    .map((s) => `${formatDuration(s.layoverMinutes ?? 0)} in ${s.from}`)
    .join(', ')
  return `${leg.stops} stop${leg.stops > 1 ? 's' : ''} · ${layovers}`
}

function stopMarkers(leg: Leg): number[] {
  return Array.from({ length: leg.stops }, (_, i) => ((i + 1) / (leg.stops + 1)) * 100)
}
</script>

<template>
  <article class="card overflow-hidden">
    <div class="grid lg:grid-cols-[1fr_220px]">
      <div class="flex flex-col gap-5 p-4 sm:p-5">
        <div v-for="(leg, i) in itinerary.legs" :key="leg.id" class="grid grid-cols-[auto_1fr] gap-x-3">
          <AirlineLogo
            :code="leg.carriers[0] ?? itinerary.validatingCarrier"
            :name="airlineName(leg.carriers[0] ?? itinerary.validatingCarrier)"
          />
          <div class="min-w-0">
            <p class="flex min-w-0 items-center gap-2">
              <span v-if="legLabels[i]" class="tag tag-neutral h-5 shrink-0 px-1.5 text-[11px] uppercase tracking-wide">{{ legLabels[i] }}</span>
              <span class="truncate text-[15px] font-semibold text-ink">{{ leg.carriers.map(airlineName).join(' + ') }}</span>
            </p>
            <div class="mt-2 grid grid-cols-[auto_1fr_auto] items-center gap-3 sm:gap-4">
              <div>
                <p class="tabular font-display text-xl font-bold leading-none sm:text-2xl">{{ formatTime(leg.departAt) }}</p>
                <p class="mt-1 text-xs font-semibold text-ink-2" :title="airports[leg.from]?.name">{{ leg.from }}</p>
              </div>
              <div class="min-w-0 text-center">
                <p class="text-xs text-ink-3">{{ formatDuration(leg.durationMinutes) }}</p>
                <div class="relative my-1.5 h-px bg-line-strong" aria-hidden="true">
                  <span
                    v-for="pos in stopMarkers(leg)"
                    :key="pos"
                    class="absolute top-1/2 h-2 w-2 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-surface bg-amber"
                    :style="{ left: `${pos}%` }"
                  />
                </div>
                <p class="truncate text-xs" :class="leg.stops === 0 ? 'font-semibold text-jade' : 'text-ink-2'">{{ stopsText(leg) }}</p>
              </div>
              <div class="text-right">
                <p class="tabular font-display text-xl font-bold leading-none sm:text-2xl">
                  {{ formatTime(leg.arriveAt) }}<sup
                    v-if="dayOffset(leg.departAt, leg.arriveAt) > 0"
                    class="ml-0.5 align-super text-[11px] font-semibold text-amber"
                    :aria-label="`arrives ${dayOffset(leg.departAt, leg.arriveAt)} day later`"
                  >+{{ dayOffset(leg.departAt, leg.arriveAt) }}</sup>
                </p>
                <p class="mt-1 text-xs font-semibold text-ink-2" :title="airports[leg.to]?.name">{{ leg.to }}</p>
              </div>
            </div>
          </div>
        </div>

        <div class="flex flex-wrap gap-2">
          <span v-if="itinerary.refundable" class="tag tag-jade">Refundable</span>
          <span v-else class="tag tag-neutral">Non-refundable</span>
          <span v-if="itinerary.seatsLeft !== null && itinerary.seatsLeft <= 4" class="tag tag-rose">
            {{ itinerary.seatsLeft }} seat{{ itinerary.seatsLeft === 1 ? '' : 's' }} left
          </span>
          <span class="tag tag-neutral">{{ itinerary.baggage.checked ? `Checked bag: ${itinerary.baggage.checked}` : 'Baggage not stated' }}</span>
        </div>
      </div>

      <div
        class="stub flex items-center justify-between gap-3 border-t border-dashed border-line p-4 sm:p-5 lg:flex-col lg:items-end lg:justify-center lg:border-l lg:border-t-0"
      >
        <div class="lg:text-right">
          <p class="tabular font-display text-2xl font-bold">{{ formatMoney(itinerary.price.total, itinerary.price.currency) }}</p>
          <p class="text-xs text-ink-3">
            {{ formatMoney(itinerary.price.perAdult, itinerary.price.currency) }} per adult
          </p>
        </div>
        <RouterLink
          :to="{ name: 'detail', params: { searchId, itineraryId: itinerary.id } }"
          class="btn btn-primary"
        >
          View details
        </RouterLink>
      </div>
    </div>
  </article>
</template>
