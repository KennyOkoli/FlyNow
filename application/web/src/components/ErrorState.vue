<script setup lang="ts">
defineProps<{ title: string; message?: string; retryLabel?: string }>()
const emit = defineEmits<{ retry: [] }>()
</script>

<template>
  <div class="card flex flex-col items-start gap-3 border-rose/30 p-6 sm:p-8" role="alert">
    <span class="tag tag-rose">Something went wrong</span>
    <h2 class="text-xl font-semibold">{{ title }}</h2>
    <p v-if="message" class="max-w-prose text-sm text-ink-2">{{ message }}</p>
    <div class="mt-2 flex flex-wrap gap-3">
      <button type="button" class="btn btn-primary" @click="emit('retry')">{{ retryLabel ?? 'Try again' }}</button>
      <slot />
    </div>
  </div>
</template>
