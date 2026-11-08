<script setup lang="ts">
import { computed, nextTick, reactive, ref } from 'vue'
import type { Airport, Cabin, Passengers, SearchRequest, TripType } from '../api/types'
import { AIRPORTS } from '../data/airports'
import { CABINS, TRIP_TYPES } from '../data/options'
import { useSearchStore } from '../stores/search'
import { addDays, todayYmd } from '../utils/format'
import AirportField from './AirportField.vue'
import PassengersPopover from './PassengersPopover.vue'

const props = defineProps<{ initial?: SearchRequest | null }>()
const emit = defineEmits<{ submit: [request: SearchRequest] }>()
const store = useSearchStore()

const today = todayYmd()

const form = reactive({
  tripType: 'roundtrip' as TripType,
  origin: null as Airport | null,
  destination: null as Airport | null,
  departDate: addDays(today, 7),
  returnDate: addDays(today, 14),
  passengers: { adults: 1, children: 0, infants: 0 } as Passengers,
  cabin: 'economy' as Cabin,
})
const attempted = ref(false)
const departInput = ref<HTMLInputElement | null>(null)

function resolveAirport(code: string): Airport {
  return store.knownAirports[code] ?? AIRPORTS[code] ?? { iata: code, city: code, name: '', country: '' }
}

function applyInitial(q: SearchRequest) {
  form.tripType = q.tripType
  form.origin = resolveAirport(q.origin)
  form.destination = resolveAirport(q.destination)
  form.departDate = q.departDate
  if (q.returnDate) form.returnDate = q.returnDate
  form.passengers = { ...q.passengers }
  form.cabin = q.cabin
}

if (props.initial) applyInitial(props.initial)

function prefill(values: { origin?: Airport; destination?: Airport; fallbackOrigin?: Airport }) {
  if (values.origin) form.origin = values.origin
  else if (!form.origin && values.fallbackOrigin) form.origin = values.fallbackOrigin
  if (values.destination) form.destination = values.destination
  nextTick(() => departInput.value?.focus({ preventScroll: true }))
}

defineExpose({ prefill })

const isRoundTrip = computed(() => form.tripType === 'roundtrip')
const returnMin = computed(() => (form.departDate >= today ? form.departDate : today))

type Field = 'origin' | 'destination' | 'departDate' | 'returnDate'

const errors = computed<Partial<Record<Field, string>>>(() => {
  const e: Partial<Record<Field, string>> = {}
  if (!form.origin) e.origin = 'Choose a departure airport from the list.'
  if (!form.destination) e.destination = 'Choose an arrival airport from the list.'
  else if (form.origin && form.origin.iata === form.destination.iata) e.destination = 'Arrival must be a different airport from departure.'
  if (!form.departDate) e.departDate = 'Pick a departure date.'
  else if (form.departDate < today) e.departDate = 'Departure date must be today or later.'
  if (isRoundTrip.value) {
    if (!form.returnDate) e.returnDate = 'Pick a return date.'
    else if (form.departDate && form.returnDate < form.departDate) e.returnDate = 'Return date must be on or after departure.'
  }
  return e
})

const shown = computed<Partial<Record<Field, string>>>(() => (attempted.value ? errors.value : {}))

function swap() {
  const origin = form.origin
  form.origin = form.destination
  form.destination = origin
}

function onSubmit() {
  attempted.value = true
  if (Object.keys(errors.value).length || !form.origin || !form.destination) return
  const request: SearchRequest = {
    tripType: form.tripType,
    origin: form.origin.iata,
    destination: form.destination.iata,
    departDate: form.departDate,
    passengers: { ...form.passengers },
    cabin: form.cabin,
  }
  if (isRoundTrip.value) request.returnDate = form.returnDate
  store.rememberAirports([form.origin, form.destination])
  emit('submit', request)
}
</script>

<template>
  <form class="card p-4 shadow-float sm:p-6" novalidate aria-labelledby="search-form-title" @submit.prevent="onSubmit">
    <h2 id="search-form-title" class="sr-only">Search flights</h2>

    <div role="tablist" aria-label="Trip type" class="inline-flex rounded-[10px] bg-paper p-1">
      <button
        v-for="t in TRIP_TYPES"
        :key="t.value"
        type="button"
        role="tab"
        :aria-selected="form.tripType === t.value"
        class="h-9 rounded-[7px] px-4 text-sm font-semibold transition-colors"
        :class="form.tripType === t.value ? 'bg-surface text-ink shadow-sm' : 'text-ink-2 hover:text-ink'"
        @click="form.tripType = t.value"
      >
        {{ t.label }}
      </button>
    </div>

    <div class="mt-4 grid gap-3 md:grid-cols-2 lg:grid-cols-[1fr_auto_1fr_minmax(10rem,0.7fr)_minmax(10rem,0.7fr)] lg:items-start">
      <AirportField id="origin" v-model="form.origin" label="From" placeholder="City or airport" :error="shown.origin" />

      <div class="flex justify-center md:col-span-2 lg:col-span-1 lg:pt-[31px]">
        <button
          type="button"
          class="stepper h-9 w-9 text-ink-2"
          aria-label="Swap departure and arrival airports"
          @click="swap"
        >
          <svg class="h-4 w-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M2 5h12m0 0-3-3m3 3-3 3M14 11H2m0 0 3-3m-3 3 3 3" />
          </svg>
        </button>
      </div>

      <AirportField id="destination" v-model="form.destination" label="To" placeholder="City or airport" :error="shown.destination" />

      <div>
        <label for="depart-date" class="field-label">Depart</label>
        <input
          id="depart-date"
          ref="departInput"
          v-model="form.departDate"
          type="date"
          class="input"
          :min="today"
          :aria-invalid="shown.departDate ? 'true' : undefined"
          :aria-describedby="shown.departDate ? 'depart-date-error' : undefined"
        />
        <p v-if="shown.departDate" id="depart-date-error" class="field-error">{{ shown.departDate }}</p>
      </div>

      <div>
        <label for="return-date" class="field-label">Return</label>
        <input
          id="return-date"
          v-model="form.returnDate"
          type="date"
          class="input"
          :min="returnMin"
          :disabled="!isRoundTrip"
          :aria-invalid="shown.returnDate ? 'true' : undefined"
          :aria-describedby="!isRoundTrip ? 'return-date-hint' : shown.returnDate ? 'return-date-error' : undefined"
        />
        <p v-if="!isRoundTrip" id="return-date-hint" class="mt-1.5 text-xs text-ink-3">Not needed for a one-way trip.</p>
        <p v-else-if="shown.returnDate" id="return-date-error" class="field-error">{{ shown.returnDate }}</p>
      </div>
    </div>

    <div class="mt-3 grid gap-3 md:grid-cols-2 lg:grid-cols-[1fr_1fr_auto] lg:items-end">
      <PassengersPopover id="passengers" v-model="form.passengers" />

      <div>
        <label for="cabin" class="field-label">Cabin</label>
        <select id="cabin" v-model="form.cabin" class="input select">
          <option v-for="c in CABINS" :key="c.value" :value="c.value">{{ c.label }}</option>
        </select>
      </div>

      <button type="submit" class="btn btn-primary h-12 px-8 md:col-span-2 lg:col-span-1">Search flights</button>
    </div>
  </form>
</template>
