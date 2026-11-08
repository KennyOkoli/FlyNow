<script setup lang="ts">
withDefaults(defineProps<{ legs?: number }>(), { legs: 1 })
</script>

<template>
  <div class="card overflow-hidden" aria-hidden="true">
    <div class="grid lg:grid-cols-[1fr_220px]">
      <div class="flex flex-col gap-5 p-4 sm:p-5">
        <div v-for="n in legs" :key="n" class="grid grid-cols-[auto_1fr] gap-x-3">
          <div class="skeleton h-10 w-10 rounded-lg" />
          <div class="flex flex-col gap-3">
            <div class="skeleton h-3 w-32" />
            <div class="grid grid-cols-[auto_1fr_auto] items-center gap-4">
              <div class="skeleton h-7 w-16" />
              <div class="skeleton h-px" />
              <div class="skeleton h-7 w-16" />
            </div>
            <div class="skeleton h-3 w-44" />
          </div>
        </div>
        <div class="flex gap-2">
          <div class="skeleton h-6 w-24" />
          <div class="skeleton h-6 w-28" />
        </div>
      </div>
      <div class="flex items-center justify-between gap-3 border-t border-dashed border-line p-4 sm:p-5 lg:flex-col lg:items-end lg:justify-center lg:border-l lg:border-t-0">
        <div class="skeleton h-8 w-28" />
        <div class="skeleton h-11 w-32 rounded-[10px]" />
      </div>
    </div>
  </div>
</template>
