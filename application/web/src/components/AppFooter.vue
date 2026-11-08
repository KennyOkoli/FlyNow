<script setup lang="ts">
import { brand } from '../brand'
import BrandMark from './BrandMark.vue'

const year = new Date().getFullYear()
</script>

<template>
  <footer class="mt-auto border-t border-line bg-surface">
    <div class="container-x flex flex-col gap-6 py-10 sm:flex-row sm:items-start sm:justify-between">
      <div class="max-w-sm">
        <div class="flex items-center gap-2.5">
          <BrandMark class="h-7 w-7" />
          <span class="font-display text-lg font-bold tracking-tight">{{ brand.name }}</span>
        </div>
        <p class="mt-3 text-sm text-ink-2">{{ brand.tagline }}. Fares come straight from airline inventory and are refreshed every time you search.</p>
      </div>
      <nav aria-label="Footer" class="flex flex-col gap-2 text-sm">
        <RouterLink to="/" class="rounded-md text-ink-2 hover:text-ink">Search flights</RouterLink>
        <RouterLink to="/#popular-routes" class="rounded-md text-ink-2 hover:text-ink">Popular routes</RouterLink>
      </nav>
    </div>
    <div class="border-t border-line">
      <div class="container-x flex flex-col gap-1 py-4 text-xs text-ink-3 sm:flex-row sm:justify-between">
        <span>{{ year }} {{ brand.name }}. Flight search only; booking is not available yet.</span>
        <span>Prices shown include taxes and fees known at search time.</span>
      </div>
    </div>
  </footer>
</template>
