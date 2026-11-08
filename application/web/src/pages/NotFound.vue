<script setup lang="ts">
import AppHeader from '../components/AppHeader.vue'
import EmptyState from '../components/EmptyState.vue'
</script>

<template>
  <div class="flex min-h-dvh flex-col">
    <AppHeader />
    <main class="container-x flex-1 py-12">
      <EmptyState title="This page took a different route" body="The page you were looking for does not exist or has moved.">
        <RouterLink to="/" class="btn btn-primary">Search flights</RouterLink>
      </EmptyState>
    </main>
  </div>
</template>
