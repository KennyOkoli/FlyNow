<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { brand } from '../brand'

defineProps<{ from: string; to: string; fromCity?: string; toCity?: string }>()

const MESSAGES = ['Checking airlines', 'Comparing fares', 'Finding the best connections', 'Almost there']
const step = ref(0)
let timer: number | undefined

onMounted(() => {
  timer = window.setInterval(() => {
    step.value = Math.min(step.value + 1, MESSAGES.length - 1)
  }, 1800)
})

onBeforeUnmount(() => window.clearInterval(timer))
</script>

<template>
  <div class="preloader fixed inset-0 z-50 flex flex-col items-center justify-center bg-ink px-4 text-white" role="status" aria-live="polite">
    <p class="sr-only">Searching for flights from {{ fromCity ?? from }} to {{ toCity ?? to }}. {{ MESSAGES[step] }}.</p>

    <div class="sky relative h-48 w-full max-w-lg overflow-hidden" aria-hidden="true">
      <svg class="cloud cloud-a" viewBox="0 0 120 48"><path d="M22 44h78a18 18 0 0 0 0-36 26 26 0 0 0-49-2A20 20 0 0 0 22 44Z" /></svg>
      <svg class="cloud cloud-b" viewBox="0 0 120 48"><path d="M22 44h78a18 18 0 0 0 0-36 26 26 0 0 0-49-2A20 20 0 0 0 22 44Z" /></svg>
      <svg class="cloud cloud-c" viewBox="0 0 120 48"><path d="M22 44h78a18 18 0 0 0 0-36 26 26 0 0 0-49-2A20 20 0 0 0 22 44Z" /></svg>

      <div class="contrail" />

      <svg class="plane" viewBox="-14 -11 28 22">
        <path
          d="M13 0c0-1.3-1.4-2-3-2H4L-2.5-10H-6l3 8h-5.5l-2.5-3.2H-13l1.5 5.2-1.5 5.2h2l2.5-3.2H-3l-3 8h3.5L4 2h6c1.6 0 3-.7 3-2Z"
          fill="#fff"
        />
      </svg>
    </div>

    <div class="mt-2 flex items-center gap-4 font-display text-3xl font-bold tracking-tight sm:text-4xl" aria-hidden="true">
      <span>{{ from }}</span>
      <span class="dots"><i /><i /><i /></span>
      <span>{{ to }}</span>
    </div>
    <p v-if="fromCity && toCity" class="mt-1 text-sm text-white/60" aria-hidden="true">{{ fromCity }} to {{ toCity }}</p>

    <Transition name="msg" mode="out-in">
      <p :key="step" class="mt-8 text-base font-medium text-sky" aria-hidden="true">{{ MESSAGES[step] }}…</p>
    </Transition>

    <p class="absolute bottom-6 text-xs font-semibold uppercase tracking-[0.2em] text-white/35">{{ brand.name }}</p>
  </div>
</template>

<style scoped>
.sky {
  mask-image: linear-gradient(90deg, transparent, #000 22%, #000 78%, transparent);
}

.cloud {
  position: absolute;
  fill: rgba(255, 255, 255, 0.08);
  animation: drift linear infinite;
}
.cloud-a {
  width: 140px;
  top: 12%;
  animation-duration: 3.2s;
}
.cloud-b {
  width: 90px;
  top: 62%;
  animation-duration: 2.2s;
  animation-delay: -1.1s;
  fill: rgba(255, 255, 255, 0.12);
}
.cloud-c {
  width: 180px;
  top: 34%;
  animation-duration: 4.6s;
  animation-delay: -2.8s;
  fill: rgba(255, 255, 255, 0.05);
}

.plane {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 72px;
  margin: -28px 0 0 -36px;
  filter: drop-shadow(0 6px 14px rgba(125, 151, 255, 0.45));
  animation: bob 2.4s ease-in-out infinite;
}

.contrail {
  position: absolute;
  top: 50%;
  right: calc(50% + 30px);
  width: 45%;
  height: 2px;
  margin-top: -1px;
  background: linear-gradient(90deg, transparent, rgba(125, 151, 255, 0.7));
  border-radius: 2px;
  animation: bob 2.4s ease-in-out infinite;
}

.dots {
  display: inline-flex;
  gap: 6px;
}
.dots i {
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: var(--sky);
  animation: pulse 1.2s ease-in-out infinite;
}
.dots i:nth-child(2) {
  animation-delay: 0.2s;
}
.dots i:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes drift {
  from {
    transform: translateX(560px);
  }
  to {
    transform: translateX(-220px);
  }
}
@keyframes bob {
  0%,
  100% {
    transform: translateY(-6px) rotate(-2deg);
  }
  50% {
    transform: translateY(6px) rotate(2deg);
  }
}
@keyframes pulse {
  0%,
  100% {
    opacity: 0.25;
    transform: scale(0.8);
  }
  50% {
    opacity: 1;
    transform: scale(1);
  }
}

.msg-enter-active,
.msg-leave-active {
  transition:
    opacity 250ms ease,
    transform 250ms ease;
}
.msg-enter-from {
  opacity: 0;
  transform: translateY(6px);
}
.msg-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

@media (prefers-reduced-motion: reduce) {
  .cloud {
    animation: none;
    left: 30%;
  }
}
</style>
