<script setup lang="ts">
import { useDebounceFn } from '@vueuse/core'
import { computed, ref, watch } from 'vue'
import { searchAirports } from '../api/client'
import type { Airport } from '../api/types'

const props = defineProps<{ id: string; label: string; placeholder?: string; error?: string }>()
const model = defineModel<Airport | null>({ default: null })

function display(a: Airport | null): string {
  if (!a) return ''
  return a.city && a.city !== a.iata ? `${a.city} (${a.iata})` : a.iata
}

const text = ref(display(model.value))
const options = ref<Airport[]>([])
const open = ref(false)
const active = ref(-1)
const focused = ref(false)
const status = ref<'idle' | 'loading' | 'empty' | 'error'>('idle')
let controller: AbortController | null = null
let blurTimer: number | undefined

watch(model, (v) => {
  if (!focused.value) text.value = display(v)
})

const listId = computed(() => `${props.id}-listbox`)
const errorId = computed(() => `${props.id}-error`)
const optionId = (i: number) => `${props.id}-option-${i}`

const fetchOptions = useDebounceFn(async (q: string) => {
  controller?.abort()
  controller = new AbortController()
  status.value = 'loading'
  try {
    const list = await searchAirports(q, 8, controller.signal)
    options.value = list
    active.value = list.length ? 0 : -1
    status.value = list.length ? 'idle' : 'empty'
    open.value = focused.value
  } catch (e) {
    if (e instanceof DOMException && e.name === 'AbortError') return
    options.value = []
    active.value = -1
    status.value = 'error'
    open.value = focused.value
  }
}, 200)

function onInput(e: Event) {
  const q = (e.target as HTMLInputElement).value
  text.value = q
  if (model.value) model.value = null
  if (q.trim().length >= 2) {
    fetchOptions(q.trim())
  } else {
    controller?.abort()
    options.value = []
    active.value = -1
    status.value = 'idle'
    open.value = false
  }
}

function select(a: Airport) {
  model.value = a
  text.value = display(a)
  open.value = false
  options.value = []
  active.value = -1
}

function onKeydown(e: KeyboardEvent) {
  const count = options.value.length
  switch (e.key) {
    case 'ArrowDown':
      e.preventDefault()
      if (!count) return
      open.value = true
      active.value = (active.value + 1) % count
      break
    case 'ArrowUp':
      e.preventDefault()
      if (!count) return
      open.value = true
      active.value = (active.value - 1 + count) % count
      break
    case 'Enter': {
      if (!open.value || active.value < 0) return
      e.preventDefault()
      const opt = options.value[active.value]
      if (opt) select(opt)
      break
    }
    case 'Escape':
      if (open.value) {
        e.preventDefault()
        open.value = false
      }
      break
  }
}

function onFocus() {
  window.clearTimeout(blurTimer)
  focused.value = true
  if (options.value.length || status.value !== 'idle') open.value = true
}

function onBlur() {
  blurTimer = window.setTimeout(() => {
    focused.value = false
    open.value = false
    text.value = display(model.value)
  }, 120)
}
</script>

<template>
  <div class="relative">
    <label :for="id" class="field-label">{{ label }}</label>
    <input
      :id="id"
      class="input"
      type="text"
      role="combobox"
      autocomplete="off"
      autocapitalize="off"
      spellcheck="false"
      :placeholder="placeholder"
      :value="text"
      :aria-expanded="open"
      :aria-controls="listId"
      :aria-activedescendant="open && active >= 0 ? optionId(active) : undefined"
      aria-autocomplete="list"
      :aria-invalid="error ? 'true' : undefined"
      :aria-describedby="error ? errorId : undefined"
      @input="onInput"
      @keydown="onKeydown"
      @focus="onFocus"
      @blur="onBlur"
    />
    <ul
      v-show="open"
      :id="listId"
      role="listbox"
      :aria-label="`${label} suggestions`"
      class="card absolute z-30 mt-1 max-h-72 w-full min-w-[18rem] overflow-y-auto py-1 shadow-pop sm:w-max sm:max-w-md"
    >
      <li
        v-for="(a, i) in options"
        :id="optionId(i)"
        :key="a.iata"
        role="option"
        :aria-selected="i === active"
        class="cursor-pointer px-3 py-2 text-sm"
        :class="i === active ? 'bg-cobalt-tint' : ''"
        @mousedown.prevent="select(a)"
        @mousemove="active = i"
      >
        <span class="font-semibold">{{ a.city }} ({{ a.iata }})</span>
        <span class="text-ink-2"> — {{ a.name }}</span>
      </li>
      <li v-if="status === 'loading' && !options.length" class="px-3 py-2 text-sm text-ink-3" role="presentation">Searching airports…</li>
      <li v-else-if="status === 'empty'" class="px-3 py-2 text-sm text-ink-3" role="presentation">No airports match "{{ text }}".</li>
      <li v-else-if="status === 'error'" class="px-3 py-2 text-sm text-rose" role="presentation">Couldn't load airports. Keep typing to retry.</li>
    </ul>
    <p v-if="error" :id="errorId" class="field-error">{{ error }}</p>
  </div>
</template>
