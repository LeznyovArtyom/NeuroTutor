import { createRouter, createWebHistory } from 'vue-router'
import ChatPage from '@/components/pages/ChatPage.vue'
import IndexPage from '@/components/pages/IndexPage.vue'
import AuthorizationPage from '@/components/pages/AuthorizationPage.vue'
import RegistrationPage from '@/components/pages/RegistrationPage.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'Индекс',
      component: IndexPage,
    },
    {
      path: '/authorization',
      name: 'Авторизация',
      component: AuthorizationPage,
    },
    {
      path: '/registration',
      name: 'Регистрация',
      component: RegistrationPage,
    },
    {
      path: '/chat',
      name: 'Чат',
      component: ChatPage,
    }
  ],
})

export default router
