import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: () => import('../views/HomeView.vue') },
    { path: '/projects/new', name: 'project-new', component: () => import('../views/ProjectCreateView.vue') },
    { path: '/projects/:id', name: 'project-detail', component: () => import('../views/ProjectDetailView.vue') },
    { path: '/projects/:id/storyboard', name: 'storyboard', component: () => import('../views/StoryboardView.vue') }
  ]
})

export default router
