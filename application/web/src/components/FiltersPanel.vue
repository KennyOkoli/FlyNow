<script setup lang="ts">
import { TIME_BUCKETS, formatDuration, formatMoney } from '../utils/format'
import { STOP_FILTERS, activeFilterCount, emptyFilters, type FilterOptions, type Filters } from '../utils/filters'

defineProps<{ options: FilterOptions }>()
const filters = defineModel<Filters>({ required: true })

function toggle<T>(list: T[], value: T): T[] {
  return list.includes(value) ? list.filter((v) => v !== value) : [...list, value]
}

function setNumber(key: 'priceMin' | 'priceMax' | 'maxDuration', raw: string) {
  const n = raw === '' ? null : Number(raw)
  filters.value = { ...filters.value, [key]: n === null || Number.isNaN(n) ? null : n }
}

function clear() {
  filters.value = emptyFilters()
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="flex items-center justify-between">
      <h2 class="text-lg font-semibold">Filters</h2>
      <button
        v-if="activeFilterCount(filters)"
        type="button"
        class="text-sm font-semibold text-cobalt hover:underline"
        @click="clear"
      >
        Clear all
      </button>
    </div>

    <fieldset>
      <legend class="field-label">Stops</legend>
      <label v-for="s in STOP_FILTERS" :key="s.id" class="flex items-center justify-between gap-3 py-1.5 text-sm">
        <span class="flex items-center gap-2.5">
          <input
            type="checkbox"
            class="checkbox"
            :checked="filters.stops.includes(s.id)"
            :disabled="options.stopCounts[s.id] === 0"
            @change="filters = { ...filters, stops: toggle(filters.stops, s.id) }"
          />
          {{ s.label }}
        </span>
        <span class="tabular text-xs text-ink-3">{{ options.stopCounts[s.id] }}</span>
      </label>
    </fieldset>

    <fieldset>
      <legend class="field-label">Airlines</legend>
      <div class="max-h-56 overflow-y-auto pr-1">
        <label v-for="a in options.airlines" :key="a.code" class="flex items-center justify-between gap-3 py-1.5 text-sm">
          <span class="flex min-w-0 items-center gap-2.5">
            <input
              type="checkbox"
              class="checkbox shrink-0"
              :checked="filters.airlines.includes(a.code)"
              @change="filters = { ...filters, airlines: toggle(filters.airlines, a.code) }"
            />
            <span class="truncate">{{ a.name }}</span>
          </span>
          <span class="tabular text-xs text-ink-3">{{ a.count }}</span>
        </label>
      </div>
    </fieldset>

    <fieldset>
      <legend class="field-label">Price ({{ options.currency }})</legend>
      <div class="grid grid-cols-2 gap-2">
        <div>
          <label for="price-min" class="sr-only">Minimum price</label>
          <input
            id="price-min"
            type="number"
            inputmode="numeric"
            class="input h-10 text-sm"
            :placeholder="String(options.priceMin)"
            :min="options.priceMin"
            :max="options.priceMax"
            :value="filters.priceMin ?? ''"
            @change="setNumber('priceMin', ($event.target as HTMLInputElement).value)"
          />
        </div>
        <div>
          <label for="price-max" class="sr-only">Maximum price</label>
          <input
            id="price-max"
            type="number"
            inputmode="numeric"
            class="input h-10 text-sm"
            :placeholder="String(options.priceMax)"
            :min="options.priceMin"
            :max="options.priceMax"
            :value="filters.priceMax ?? ''"
            @change="setNumber('priceMax', ($event.target as HTMLInputElement).value)"
          />
        </div>
      </div>
      <p class="mt-1.5 text-xs text-ink-3">
        From {{ formatMoney(options.priceMin, options.currency) }} to {{ formatMoney(options.priceMax, options.currency) }}
      </p>
    </fieldset>

    <fieldset>
      <legend class="field-label">Departure time (outbound)</legend>
      <div class="grid grid-cols-2 gap-2">
        <button
          v-for="b in TIME_BUCKETS"
          :key="b.id"
          type="button"
          class="rounded-[10px] border px-3 py-2 text-left text-sm transition-colors"
          :class="filters.departBuckets.includes(b.id) ? 'border-cobalt bg-cobalt-tint text-cobalt' : 'border-line bg-surface hover:border-line-strong'"
          :aria-pressed="filters.departBuckets.includes(b.id)"
          @click="filters = { ...filters, departBuckets: toggle(filters.departBuckets, b.id) }"
        >
          <span class="block font-semibold">{{ b.label }}</span>
          <span class="block text-xs text-ink-3">{{ b.range }}</span>
        </button>
      </div>
    </fieldset>

    <fieldset v-if="options.durationMax > options.durationMin">
      <legend class="field-label">Max total travel time</legend>
      <input
        type="range"
        class="range"
        aria-label="Maximum total travel time"
        :min="options.durationMin"
        :max="options.durationMax"
        step="15"
        :value="filters.maxDuration ?? options.durationMax"
        @input="setNumber('maxDuration', ($event.target as HTMLInputElement).value)"
      />
      <p class="mt-1 text-xs text-ink-3">Up to {{ formatDuration(filters.maxDuration ?? options.durationMax) }}</p>
    </fieldset>
  </div>
</template>
