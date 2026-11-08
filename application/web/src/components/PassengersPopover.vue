<script setup lang="ts">
import { onClickOutside } from '@vueuse/core'
import { computed, ref } from 'vue'
import type { Passengers } from '../api/types'
import { formatPassengers, totalPassengers } from '../utils/format'

defineProps<{ id: string }>()
const model = defineModel<Passengers>({ required: true })

const root = ref<HTMLElement | null>(null)
const trigger = ref<HTMLButtonElement | null>(null)
const open = ref(false)

onClickOutside(root, () => {
  open.value = false
})

type Key = keyof Passengers

const rows: { key: Key; label: string; hint: string }[] = [
  { key: 'adults', label: 'Adults', hint: '12 years and over' },
  { key: 'children', label: 'Children', hint: '2 to 11 years' },
  { key: 'infants', label: 'Infants', hint: 'Under 2, on an adult’s lap' },
]

const total = computed(() => totalPassengers(model.value))
const summary = computed(() => formatPassengers(model.value))

function canIncrease(key: Key): boolean {
  if (total.value >= 9) return false
  if (key === 'adults') return model.value.adults < 9
  if (key === 'children') return model.value.children < 8
  return model.value.infants < model.value.adults
}

function canDecrease(key: Key): boolean {
  if (key === 'adults') return model.value.adults > 1
  return model.value[key] > 0
}

function step(key: Key, delta: number) {
  if (delta > 0 && !canIncrease(key)) return
  if (delta < 0 && !canDecrease(key)) return
  const next = { ...model.value, [key]: model.value[key] + delta }
  if (next.infants > next.adults) next.infants = next.adults
  model.value = next
}

function close() {
  open.value = false
  trigger.value?.focus()
}
</script>

<template>
  <div ref="root" class="relative">
    <span :id="`${id}-label`" class="field-label">Passengers</span>
    <button
      :id="id"
      ref="trigger"
      type="button"
      class="input flex items-center justify-between text-left"
      aria-haspopup="dialog"
      :aria-expanded="open"
      :aria-controls="`${id}-dialog`"
      :aria-labelledby="`${id}-label ${id}`"
      @click="open = !open"
    >
      <span>{{ summary }}</span>
      <svg class="h-4 w-4 text-ink-2" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="m4 6 4 4 4-4" />
      </svg>
    </button>

    <div
      v-if="open"
      :id="`${id}-dialog`"
      role="dialog"
      aria-label="Passengers"
      class="card absolute z-30 mt-1 w-full min-w-[19rem] p-4 shadow-pop"
      @keydown.escape.prevent="close"
    >
      <div v-for="row in rows" :key="row.key" class="flex items-center justify-between border-b border-line py-3 last:border-0">
        <div>
          <p class="text-sm font-semibold">{{ row.label }}</p>
          <p class="text-xs text-ink-3">{{ row.hint }}</p>
        </div>
        <div class="flex items-center gap-3">
          <button
            type="button"
            class="stepper"
            :aria-label="`Fewer ${row.label.toLowerCase()}`"
            :disabled="!canDecrease(row.key)"
            @click="step(row.key, -1)"
          >
            &minus;
          </button>
          <span class="tabular w-5 text-center font-semibold" aria-live="polite">{{ model[row.key] }}</span>
          <button
            type="button"
            class="stepper"
            :aria-label="`More ${row.label.toLowerCase()}`"
            :disabled="!canIncrease(row.key)"
            @click="step(row.key, 1)"
          >
            +
          </button>
        </div>
      </div>
      <p class="mt-3 text-xs text-ink-3">Up to 9 passengers per booking. Each infant needs an adult.</p>
      <button type="button" class="btn btn-secondary mt-3 h-10 w-full" @click="close">Done</button>
    </div>
  </div>
</template>
