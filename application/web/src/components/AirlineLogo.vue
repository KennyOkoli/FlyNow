<script setup lang="ts">
import { ref, watch } from 'vue'
import CarrierBadge from './CarrierBadge.vue'

const props = withDefaults(defineProps<{ code: string; name?: string; size?: 'sm' | 'md' }>(), { size: 'md' })

const failed = ref(false)
watch(
  () => props.code,
  () => (failed.value = false),
)
</script>

<template>
  <span
    class="inline-flex shrink-0 items-center justify-center overflow-hidden rounded-lg border border-line bg-white"
    :class="size === 'sm' ? 'h-8 w-16 px-1' : 'h-9 w-16 px-1 sm:h-11 sm:w-[88px] sm:px-1.5'"
  >
    <CarrierBadge v-if="failed" :code="code" size="sm" />
    <img
      v-else
      :src="`https://pics.avs.io/240/80/${code}.png`"
      :alt="name ? `${name} logo` : `${code} logo`"
      class="h-full w-full object-contain"
      loading="lazy"
      decoding="async"
      @error="failed = true"
    />
  </span>
</template>
