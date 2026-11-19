<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import type { SearchRequest } from '../api/types'
import AppFooter from '../components/AppFooter.vue'
import AppHeader from '../components/AppHeader.vue'
import DestinationsCarousel from '../components/DestinationsCarousel.vue'
import SearchForm from '../components/SearchForm.vue'
import { brand } from '../brand'
import { AIRPORTS, POPULAR_ROUTES } from '../data/airports'
import type { Destination } from '../data/destinations'
import { useSearchStore } from '../stores/search'
import { toQuery } from '../utils/query'

const router = useRouter()
const store = useSearchStore()
const formRef = ref<InstanceType<typeof SearchForm> | null>(null)
const formWrap = ref<HTMLElement | null>(null)

function onSubmit(request: SearchRequest) {
  store.setLastQuery(request)
  router.push({ name: 'results', query: toQuery(request) })
}

function pickRoute(from: string, to: string) {
  const origin = AIRPORTS[from]
  const destination = AIRPORTS[to]
  if (!origin || !destination) return
  formRef.value?.prefill({ origin, destination })
  formWrap.value?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

function pickDestination(d: Destination) {
  const destination = AIRPORTS[d.iata] ?? { iata: d.iata, city: d.city, name: '', country: d.country }
  formRef.value?.prefill({ destination, fallbackOrigin: AIRPORTS.LOS })
  formWrap.value?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

const reasons = [
  { title: 'Live fares from the airlines', body: 'Prices come straight from global distribution data, not scraped estimates.' },
  { title: 'Every leg laid out', body: 'See layovers, terminals, aircraft and baggage before you decide.' },
  { title: 'Priced for Nigerian travellers', body: 'Built around departures from Lagos, Abuja and Port Harcourt.' },
]
</script>

<template>
  <div class="flex min-h-dvh flex-col">
    <AppHeader tone="ink" />

    <main class="flex-1">
      <section class="relative overflow-hidden bg-ink pb-40 pt-12 text-white sm:pt-16">
        <svg
          class="pointer-events-none absolute inset-x-0 bottom-10 mx-auto h-48 w-full max-w-5xl text-sky/40"
          viewBox="0 0 1000 200"
          fill="none"
          aria-hidden="true"
        >
          <path class="route-arc" pathLength="1" d="M40 170 Q500 -60 960 150" stroke="currentColor" stroke-width="2" stroke-dasharray="1" />
          <circle class="route-dot" cx="40" cy="170" r="5" fill="currentColor" />
          <circle class="route-dot route-dot-end" cx="960" cy="150" r="5" fill="currentColor" />
        </svg>
        <div class="container-x relative">
          <p class="text-sm font-semibold uppercase tracking-[0.14em] text-sky">{{ brand.tagline }}</p>
          <h1 class="mt-3 max-w-2xl text-4xl font-bold sm:text-5xl">Find the flight that fits, then see every detail.</h1>
          <p class="mt-4 max-w-xl text-base text-white/75">
            Compare fares across airlines, filter by stops and times, and know your layovers before you book.
          </p>
        </div>
      </section>

      <div ref="formWrap" class="container-x relative -mt-32">
        <SearchForm ref="formRef" :initial="store.lastQuery" @submit="onSubmit" />
      </div>

      <DestinationsCarousel class="mt-16" @pick="pickDestination" />

      <section class="container-x mt-16" aria-labelledby="popular-title">
        <h2 id="popular-title" class="text-2xl font-bold">Popular routes</h2>
        <ul class="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <li v-for="r in POPULAR_ROUTES" :key="`${r.from}-${r.to}`">
            <button
              type="button"
              class="card flex w-full items-center justify-between gap-4 p-4 text-left transition-colors hover:border-cobalt"
              @click="pickRoute(r.from, r.to)"
            >
              <span>
                <span class="block font-display text-lg font-bold">
                  {{ AIRPORTS[r.from]?.city }} <span class="text-ink-3">→</span> {{ AIRPORTS[r.to]?.city }}
                </span>
                <span class="block text-sm text-ink-2">{{ r.note }}</span>
              </span>
              <span class="tag tag-neutral tabular">{{ r.from }}–{{ r.to }}</span>
            </button>
          </li>
        </ul>
      </section>

      <section class="container-x my-16" aria-labelledby="why-title">
        <h2 id="why-title" class="sr-only">Why book with {{ brand.name }}</h2>
        <ul class="grid gap-6 border-t border-line pt-10 sm:grid-cols-3">
          <li v-for="(r, i) in reasons" :key="r.title">
            <span class="tabular text-sm font-semibold text-cobalt">0{{ i + 1 }}</span>
            <h3 class="mt-2 text-lg font-semibold">{{ r.title }}</h3>
            <p class="mt-1 text-sm text-ink-2">{{ r.body }}</p>
          </li>
        </ul>
      </section>
    </main>

    <AppFooter />
  </div>
</template>
