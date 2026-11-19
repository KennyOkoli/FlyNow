<script setup lang="ts">
import { computed } from 'vue'
import { carrierColors } from '../utils/carrier'

const props = withDefaults(defineProps<{ code: string; size?: 'sm' | 'md' }>(), { size: 'md' })
const colors = computed(() => carrierColors(props.code))
</script>

<template>
  <span
    class="inline-flex shrink-0 items-center justify-center rounded-lg font-display font-bold tracking-wide"
    :class="size === 'sm' ? 'h-7 w-7 text-[11px]' : 'h-10 w-10 text-sm'"
    :style="{ background: colors.bg, color: colors.fg }"
    aria-hidden="true"
  >
    {{ code }}
  </span>
</template>
