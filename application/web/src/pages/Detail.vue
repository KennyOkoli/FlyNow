<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ApiError, getItinerary } from '../api/client'
import type { ItineraryDetail } from '../api/types'
import AppHeader from '../components/AppHeader.vue'
import EmptyState from '../components/EmptyState.vue'
import ErrorState from '../components/ErrorState.vue'
import LegTimeline from '../components/LegTimeline.vue'
import { CABIN_LABELS, PASSENGER_LABELS } from '../data/options'
import { useSearchStore } from '../stores/search'
import { formatDate, formatMoney, formatPassengers } from '../utils/format'
import { toQuery } from '../utils/query'

const props = defineProps<{ searchId: string; itineraryId: string }>()
const router = useRouter()
const store = useSearchStore()

const detail = ref<ItineraryDetail | null>(null)
const loading = ref(false)
const error = ref<ApiError | null>(null)
const showTaxes = ref(false)

async function load() {
  loading.value = true
  error.value = null
  try {
    detail.value = await getItinerary(props.searchId, props.itineraryId)
    store.rememberAirportMap(detail.value.airports)
    store.setLastQuery(detail.value.query)
  } catch (e) {
    error.value = e instanceof ApiError ? e : new ApiError(0, 'unknown', 'Something went wrong loading this flight.')
  } finally {
    loading.value = false
  }
}

watch(() => [props.searchId, props.itineraryId], load, { immediate: true })

const expired = computed(() => error.value?.code === 'search_expired')
const lastQuery = computed(() => detail.value?.query ?? store.lastQuery)
const money = (n: number) => formatMoney(n, detail.value?.price.currency ?? 'USD')

function place(code: string): string {
  return detail.value?.airports[code]?.city ?? code
}

function searchAgain() {
  const q = lastQuery.value
  if (q) router.push({ name: 'results', query: toQuery(q) })
  else router.push({ name: 'home' })
}

function backToResults() {
  if (detail.value) router.push({ name: 'results', query: toQuery(detail.value.query) })
  else router.back()
}
</script>

<template>
  <div class="flex min-h-dvh flex-col">
    <AppHeader />

    <main class="container-x flex-1 py-6">
      <button type="button" class="btn btn-ghost -ml-3 h-9 px-3 text-sm" @click="backToResults">← Back to results</button>

      <div v-if="loading" class="mt-4 flex flex-col gap-4" aria-busy="true">
        <div class="skeleton h-24 w-full rounded-[16px]" />
        <div class="skeleton h-72 w-full rounded-[16px]" />
      </div>

      <EmptyState
        v-else-if="expired"
        class="mt-4"
        title="These fares have expired"
        body="Airline prices change quickly, so we only hold search results for 30 minutes. Run the search again to see current fares."
      >
        <button type="button" class="btn btn-primary" @click="searchAgain">Search again</button>
      </EmptyState>

      <EmptyState
        v-else-if="error?.code === 'not_found'"
        class="mt-4"
        title="We could not find that flight"
        body="It may not be part of this search any more."
      >
        <button type="button" class="btn btn-primary" @click="searchAgain">Back to search</button>
      </EmptyState>

      <ErrorState v-else-if="error" class="mt-4" title="We could not load this flight" :message="error.message" @retry="load" />

      <div v-else-if="detail" class="mt-4 grid gap-6 lg:grid-cols-[1fr_340px] lg:items-start">
        <div class="flex flex-col gap-4">
          <header class="card p-4 sm:p-6">
            <p class="text-sm font-semibold text-cobalt">
              {{ detail.query.tripType === 'roundtrip' ? 'Round trip' : 'One way' }} · {{ CABIN_LABELS[detail.cabin] }}
            </p>
            <h1 class="mt-1 text-2xl font-bold sm:text-3xl">
              {{ place(detail.legs[0]!.from) }} to {{ place(detail.legs[0]!.to) }}
            </h1>
            <p class="mt-1 text-sm text-ink-2">
              {{ formatDate(detail.query.departDate, 'medium') }}<template v-if="detail.query.returnDate">
                – {{ formatDate(detail.query.returnDate, 'medium') }}</template>
              · {{ formatPassengers(detail.query.passengers) }}
            </p>
          </header>

          <LegTimeline
            v-for="(leg, i) in detail.legs"
            :key="leg.id"
            :leg="leg"
            :title="detail.legs.length > 1 ? (i === 0 ? 'Outbound' : 'Return') : 'Flight'"
            :airlines="detail.airlines"
            :airports="detail.airports"
          />

          <div v-if="detail.notes.length" class="flex flex-col gap-1">
            <p v-for="n in detail.notes" :key="n" class="small-print">{{ n }}</p>
          </div>
        </div>

        <aside class="card sticky top-6 flex flex-col gap-5 p-4 sm:p-6" aria-label="Price summary">
          <div>
            <p class="text-sm text-ink-2">Total for {{ formatPassengers(detail.query.passengers) }}</p>
            <p class="tabular font-display text-3xl font-bold">{{ money(detail.price.total) }}</p>
          </div>

          <table class="w-full text-sm">
            <caption class="sr-only">Fare breakdown</caption>
            <thead>
              <tr class="text-left text-xs text-ink-3">
                <th scope="col" class="pb-2 font-semibold">Passenger</th>
                <th scope="col" class="pb-2 text-right font-semibold">Base each</th>
                <th scope="col" class="pb-2 text-right font-semibold">Taxes each</th>
                <th scope="col" class="pb-2 text-right font-semibold">Subtotal</th>
              </tr>
            </thead>
            <tbody class="tabular">
              <tr v-for="row in detail.fareBreakdown" :key="row.passengerType" class="border-t border-line">
                <th scope="row" class="py-2 text-left font-medium">{{ row.count }} × {{ PASSENGER_LABELS[row.passengerType] }}</th>
                <td class="py-2 text-right">{{ money(row.base) }}</td>
                <td class="py-2 text-right">{{ money(row.taxes) }}</td>
                <td class="py-2 text-right font-semibold">{{ money(row.total * row.count) }}</td>
              </tr>
            </tbody>
          </table>

          <dl class="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 border-t border-line pt-4 text-sm">
            <dt class="text-ink-2">Checked bag</dt>
            <dd class="text-right">{{ detail.baggage.checked ?? 'Not stated' }}</dd>
            <dt class="text-ink-2">Refunds</dt>
            <dd class="text-right">{{ detail.refundable ? 'Refundable' : 'Non-refundable' }}</dd>
            <template v-if="detail.lastTicketDate">
              <dt class="text-ink-2">Ticket by</dt>
              <dd class="text-right">{{ formatDate(detail.lastTicketDate, 'medium') }}</dd>
            </template>
            <template v-if="detail.fareBasis.length">
              <dt class="text-ink-2">Fare basis</dt>
              <dd class="truncate text-right font-mono text-xs leading-5">{{ detail.fareBasis.join(', ') }}</dd>
            </template>
          </dl>

          <div v-if="detail.taxes.length" class="border-t border-line pt-4">
            <button
              type="button"
              class="flex w-full items-center justify-between text-sm font-semibold"
              :aria-expanded="showTaxes"
              aria-controls="tax-list"
              @click="showTaxes = !showTaxes"
            >
              Taxes and fees ({{ detail.taxes.length }})
              <span aria-hidden="true">{{ showTaxes ? '−' : '+' }}</span>
            </button>
            <ul v-show="showTaxes" id="tax-list" class="mt-3 flex flex-col gap-1.5 text-sm">
              <li v-for="t in detail.taxes" :key="t.code" class="flex justify-between gap-3">
                <span class="text-ink-2"><span class="font-mono text-xs">{{ t.code }}</span> {{ t.description }}</span>
                <span class="tabular shrink-0">{{ money(t.amount) }}</span>
              </li>
            </ul>
          </div>

          <div>
            <button type="button" class="btn btn-primary w-full" disabled aria-describedby="booking-soon">Continue</button>
            <p id="booking-soon" class="mt-2 text-center text-xs text-ink-3">Booking coming soon</p>
          </div>
        </aside>
      </div>
    </main>
  </div>
</template>
