<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ApiError } from '../api/client'
import type { SearchRequest, SearchResponse } from '../api/types'
import AppHeader from '../components/AppHeader.vue'
import EmptyState from '../components/EmptyState.vue'
import ErrorState from '../components/ErrorState.vue'
import FiltersPanel from '../components/FiltersPanel.vue'
import ResultCard from '../components/ResultCard.vue'
import SearchPreloader from '../components/SearchPreloader.vue'
import { AIRPORTS } from '../data/airports'
import SkeletonCard from '../components/SkeletonCard.vue'
import { CABIN_LABELS } from '../data/options'
import { useSearchStore } from '../stores/search'
import {
  SORT_KEYS,
  activeFilterCount,
  applyFilters,
  buildFilterOptions,
  emptyFilters,
  sortItineraries,
  type Filters,
  type SortKey,
} from '../utils/filters'
import { formatDate, formatPassengers } from '../utils/format'
import { fromQuery } from '../utils/query'

const route = useRoute()
const router = useRouter()
const store = useSearchStore()

const query = computed<SearchRequest | null>(() => fromQuery(route.query))
const response = ref<SearchResponse | null>(null)
const loading = ref(false)
const error = ref<ApiError | null>(null)
const filters = ref<Filters>(emptyFilters())
const sort = ref<SortKey>('cheapest')
const drawerOpen = ref(false)

async function run(force = false) {
  const q = query.value
  if (!q) return
  loading.value = true
  error.value = null
  try {
    response.value = await store.search(q, { force })
    filters.value = emptyFilters()
  } catch (e) {
    error.value = e instanceof ApiError ? e : new ApiError(0, 'unknown', 'Something went wrong while searching.')
    response.value = null
  } finally {
    loading.value = false
  }
}

watch(() => route.fullPath, () => run(), { immediate: true })

const options = computed(() =>
  response.value ? buildFilterOptions(response.value.itineraries, response.value.airlines, response.value.currency) : null,
)
const visible = computed(() =>
  response.value ? sortItineraries(applyFilters(response.value.itineraries, filters.value), sort.value) : [],
)
const filterCount = computed(() => activeFilterCount(filters.value))

function cityOf(code: string): string | undefined {
  return response.value?.airports[code]?.city ?? store.knownAirports[code]?.city ?? AIRPORTS[code]?.city
}

function place(code: string): string {
  return cityOf(code) ?? code
}

function editSearch() {
  if (query.value) store.setLastQuery(query.value)
  router.push({ name: 'home' })
}
</script>

<template>
  <div class="flex min-h-dvh flex-col">
    <AppHeader />

    <div v-if="query" class="sticky top-0 z-20 border-b border-line bg-surface/95 backdrop-blur">
      <div class="container-x flex flex-wrap items-center justify-between gap-3 py-3">
        <div class="min-w-0">
          <p class="truncate font-display text-lg font-bold">
            {{ place(query.origin) }} ({{ query.origin }})
            <span class="text-ink-3">{{ query.tripType === 'roundtrip' ? '⇄' : '→' }}</span>
            {{ place(query.destination) }} ({{ query.destination }})
          </p>
          <p class="text-sm text-ink-2">
            {{ formatDate(query.departDate) }}<template v-if="query.returnDate"> – {{ formatDate(query.returnDate) }}</template>
            · {{ formatPassengers(query.passengers) }} · {{ CABIN_LABELS[query.cabin] }}
          </p>
        </div>
        <button type="button" class="btn btn-secondary h-10" @click="editSearch">Edit search</button>
      </div>
    </div>

    <main class="container-x flex-1 py-6">
      <EmptyState
        v-if="!query"
        title="That search link is incomplete"
        body="Some details are missing or invalid. Start a new search from the home page."
      >
        <RouterLink to="/" class="btn btn-primary">New search</RouterLink>
      </EmptyState>

      <div v-else class="grid gap-6 lg:grid-cols-[280px_1fr]">
        <aside v-if="!loading && options && response?.itineraries.length" class="hidden lg:block" aria-label="Filters">
          <div class="card sticky top-24 p-5">
            <FiltersPanel v-model="filters" :options="options" />
          </div>
        </aside>
        <div v-else class="hidden lg:block" />

        <section aria-labelledby="results-title" class="min-w-0">
          <h1 id="results-title" class="sr-only">Flight results</h1>

          <div v-if="loading" class="flex flex-col gap-4" aria-busy="true">
            <SkeletonCard v-for="n in 4" :key="n" :legs="query.tripType === 'roundtrip' ? 2 : 1" />
          </div>

          <ErrorState
            v-else-if="error"
            :title="error.code === 'validation_error' ? 'We could not run that search' : 'We could not load flights'"
            :message="error.message"
            @retry="run(true)"
          >
            <button type="button" class="btn btn-secondary" @click="editSearch">Change search</button>
          </ErrorState>

          <template v-else-if="response">
            <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
              <p class="text-sm text-ink-2" aria-live="polite">
                <span class="font-semibold text-ink">{{ visible.length }}</span>
                {{ visible.length === 1 ? 'flight' : 'flights' }} found<template v-if="visible.length !== response.itineraries.length">
                  of {{ response.itineraries.length }}</template>
                <span v-if="response.meta.provider === 'mock'" class="tag tag-amber ml-2">Sample data</span>
              </p>
              <div class="flex items-center gap-2">
                <button
                  v-if="options && response.itineraries.length"
                  type="button"
                  class="btn btn-secondary h-10 lg:hidden"
                  @click="drawerOpen = true"
                >
                  Filters<span v-if="filterCount" class="tag tag-neutral h-5 px-1.5">{{ filterCount }}</span>
                </button>
                <div role="tablist" aria-label="Sort results" class="inline-flex rounded-[10px] bg-surface p-1 ring-1 ring-line">
                  <button
                    v-for="s in SORT_KEYS"
                    :key="s.id"
                    type="button"
                    role="tab"
                    :aria-selected="sort === s.id"
                    class="h-8 rounded-[7px] px-3 text-sm font-semibold transition-colors"
                    :class="sort === s.id ? 'bg-cobalt text-white' : 'text-ink-2 hover:text-ink'"
                    @click="sort = s.id"
                  >
                    {{ s.label }}
                  </button>
                </div>
              </div>
            </div>

            <EmptyState
              v-if="!response.itineraries.length"
              title="No flights for these dates"
              body="Airlines returned nothing for this route and date. Try nearby dates or another airport."
            >
              <button type="button" class="btn btn-primary" @click="editSearch">Change search</button>
            </EmptyState>

            <EmptyState
              v-else-if="!visible.length"
              title="No flights match your filters"
              body="Loosen a filter or clear them all to see every result."
            >
              <button type="button" class="btn btn-primary" @click="filters = emptyFilters()">Clear filters</button>
            </EmptyState>

            <ul v-else class="flex flex-col gap-4">
              <li v-for="it in visible" :key="it.id">
                <ResultCard
                  :itinerary="it"
                  :search-id="response.searchId"
                  :airlines="response.airlines"
                  :airports="response.airports"
                />
              </li>
            </ul>
          </template>
        </section>
      </div>
    </main>

    <Transition name="preloader">
      <SearchPreloader
        v-if="loading && query"
        :from="query.origin"
        :to="query.destination"
        :from-city="cityOf(query.origin)"
        :to-city="cityOf(query.destination)"
      />
    </Transition>

    <Transition name="fade">
      <div v-if="drawerOpen" class="fixed inset-0 z-40 bg-ink/40 lg:hidden" @click="drawerOpen = false" />
    </Transition>
    <Transition name="drawer">
      <div
        v-if="drawerOpen && options"
        class="fixed inset-x-0 bottom-0 z-50 max-h-[85dvh] overflow-y-auto rounded-t-[16px] bg-surface p-5 lg:hidden"
        role="dialog"
        aria-modal="true"
        aria-label="Filters"
      >
        <FiltersPanel v-model="filters" :options="options" />
        <button type="button" class="btn btn-primary mt-6 w-full" @click="drawerOpen = false">
          Show {{ visible.length }} {{ visible.length === 1 ? 'flight' : 'flights' }}
        </button>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.preloader-enter-active {
  transition: opacity 150ms ease;
}
.preloader-leave-active {
  transition: opacity 400ms ease;
}
.preloader-enter-from,
.preloader-leave-to {
  opacity: 0;
}
</style>
