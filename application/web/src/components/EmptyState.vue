<script setup lang="ts">
defineProps<{ title: string; body?: string }>()
</script>

<template>
  <div class="card flex flex-col items-start gap-3 p-6 sm:p-8">
    <svg class="h-10 w-10 text-ink-3" viewBox="0 0 40 40" fill="none" aria-hidden="true">
      <circle cx="20" cy="20" r="17" stroke="currentColor" stroke-width="1.5" stroke-dasharray="3 5" />
      <path d="M12 26 Q20 8 29 24" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
    </svg>
    <h2 class="text-xl font-semibold">{{ title }}</h2>
    <p v-if="body" class="max-w-prose text-sm text-ink-2">{{ body }}</p>
    <div v-if="$slots.default" class="mt-2 flex flex-wrap gap-3">
      <slot />
    </div>
  </div>
</template>
