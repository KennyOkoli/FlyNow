<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { DESTINATIONS, type Destination } from '../data/destinations'

const emit = defineEmits<{ pick: [destination: Destination] }>()

const track = ref<HTMLElement | null>(null)
const atStart = ref(true)
const atEnd = ref(false)

function update() {
  const el = track.value
  if (!el) return
  atStart.value = el.scrollLeft <= 4
  atEnd.value = el.scrollLeft + el.clientWidth >= el.scrollWidth - 4
}

function scrollByCards(direction: 1 | -1) {
  const el = track.value
  if (!el) return
  const cards = [...el.querySelectorAll<HTMLElement>('[data-card]')]
  if (!cards.length) return
  const inset = parseFloat(getComputedStyle(el).paddingLeft) || 0
  const step = cards[0]!.offsetWidth + 16
  const visible = Math.max(1, Math.floor((el.clientWidth - inset) / step))
  const current = Math.round(el.scrollLeft / step)
  const index = Math.min(Math.max(current + direction * visible, 0), cards.length - 1)
  el.scrollTo({ left: cards[index]!.offsetLeft - inset, behavior: 'smooth' })
}

onMounted(() => {
  update()
  window.addEventListener('resize', update)
})
onBeforeUnmount(() => window.removeEventListener('resize', update))
</script>

<template>
  <section aria-labelledby="destinations-title">
    <div class="container-x flex items-end justify-between gap-4">
      <div>
        <p class="text-sm font-semibold text-cobalt">Popular destinations</p>
        <h2 id="destinations-title" class="mt-1 text-2xl font-bold sm:text-3xl">Where do you want to go?</h2>
      </div>
      <div class="hidden gap-2 sm:flex">
        <button type="button" class="stepper h-10 w-10" aria-label="Previous destinations" :disabled="atStart" @click="scrollByCards(-1)">
          <svg class="h-4 w-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m10 3-5 5 5 5" /></svg>
        </button>
        <button type="button" class="stepper h-10 w-10" aria-label="Next destinations" :disabled="atEnd" @click="scrollByCards(1)">
          <svg class="h-4 w-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 3 5 5-5 5" /></svg>
        </button>
      </div>
    </div>

    <ul
      ref="track"
      class="track mt-5 flex snap-x snap-mandatory gap-4 overflow-x-auto pb-2"
      aria-label="Popular destinations"
      @scroll.passive="update"
    >
      <li v-for="d in DESTINATIONS" :key="d.iata" data-card class="w-[78%] shrink-0 snap-start sm:w-[300px]">
        <article class="group relative h-[340px] overflow-hidden rounded-[16px] bg-ink">
          <img
            :src="d.image"
            :alt="`${d.city}, ${d.country}`"
            class="absolute inset-0 h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
            loading="lazy"
            decoding="async"
          />
          <div class="absolute inset-0 bg-gradient-to-t from-ink/90 via-ink/20 to-transparent" aria-hidden="true" />

          <div class="absolute inset-x-0 bottom-0 flex flex-col gap-3 p-5 text-white">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.14em] text-white/70">{{ d.country }}</p>
              <h3 class="mt-1 text-2xl font-bold">{{ d.city }}</h3>
              <p class="mt-1 text-sm text-white/80">{{ d.blurb }}</p>
            </div>
            <button
              type="button"
              class="btn h-10 self-start bg-white px-4 text-sm text-ink hover:bg-cobalt-tint"
              :aria-label="`Search flights to ${d.city}`"
              @click="emit('pick', d)"
            >
              Find flights
              <svg class="h-4 w-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 8h10m0 0-4-4m4 4-4 4" /></svg>
            </button>
          </div>

          <a
            :href="d.credit.source"
            target="_blank"
            rel="noopener"
            class="absolute right-2 top-2 rounded bg-ink/50 px-1.5 py-0.5 text-[10px] text-white/80 hover:text-white"
          >
            Photo: {{ d.credit.artist }}, {{ d.credit.license }}
          </a>
        </article>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.track {
  scrollbar-width: none;
  scroll-padding-inline: max(16px, calc((100vw - 1120px) / 2 + 24px));
  padding-inline: max(16px, calc((100vw - 1120px) / 2 + 24px));
}
.track::-webkit-scrollbar {
  display: none;
}
</style>
