import { createRouter, createWebHistory } from 'vue-router'
import { brand } from './brand'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: () => import('./pages/Home.vue'), meta: { title: 'Search flights' } },
    { path: '/flights', name: 'results', component: () => import('./pages/Results.vue'), meta: { title: 'Flights' } },
    {
      path: '/flights/:searchId/:itineraryId',
      name: 'detail',
      component: () => import('./pages/Detail.vue'),
      props: true,
      meta: { title: 'Flight details' },
    },
    { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('./pages/NotFound.vue'), meta: { title: 'Page not found' } },
  ],
  scrollBehavior(_to, _from, saved) {
    return saved ?? { top: 0 }
  },
})

router.afterEach((to) => {
  const title = typeof to.meta.title === 'string' ? to.meta.title : ''
  document.title = title ? `${title} | ${brand.name}` : brand.name
})
