<script setup lang="ts">
import { brand } from '../brand'
import BrandMark from './BrandMark.vue'

withDefaults(defineProps<{ tone?: 'light' | 'ink' }>(), { tone: 'light' })
</script>

<template>
  <header :class="tone === 'ink' ? 'bg-ink text-white' : 'border-b border-line bg-surface text-ink'">
    <div class="container-x flex h-16 items-center justify-between">
      <RouterLink to="/" class="flex items-center gap-2.5 rounded-md" :aria-label="`${brand.name} home`">
        <BrandMark class="h-8 w-8" :class="tone === 'ink' ? 'ring-1 ring-white/20 rounded-lg' : ''" />
        <span class="font-display text-xl font-bold tracking-tight">{{ brand.name }}</span>
      </RouterLink>
      <nav aria-label="Primary">
        <RouterLink
          to="/"
          class="rounded-md text-sm font-semibold"
          :class="tone === 'ink' ? 'text-white/80 hover:text-white' : 'text-ink-2 hover:text-ink'"
        >
          Flights
        </RouterLink>
      </nav>
    </div>
  </header>
</template>
