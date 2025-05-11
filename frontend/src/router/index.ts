import { createRouter, createWebHistory } from 'vue-router'
import ChatPage from '@/components/pages/ChatPage.vue'
import IndexPage from '@/components/pages/IndexPage.vue'
import AuthorizationPage from '@/components/pages/AuthorizationPage.vue'
import RegistrationPage from '@/components/pages/RegistrationPage.vue'
import DisciplinesLayoutPage from '@/components/pages/DisciplinesLayoutPage.vue'
import BlankArea from '@/components/ui/BlankArea.vue'
import DisciplineCreate from '@/components/ui/DisciplineCreate.vue'
import DisciplineDetail from '@/components/ui/DisciplineDetail.vue'

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
      path: '/disciplines',
      name: 'Дисциплины',
      component: DisciplinesLayoutPage,
      children: [
        {
          path: '',
          name: 'blank-area',
          component: BlankArea,
          meta: { title: 'Выберите дисциплину' }
        },
        {
          path: 'new',
          name: 'discipline-new',
          component: DisciplineCreate,
          meta: { title: 'Создать дисциплину' }
        },
        {
          path: ':id(\\d+)',
          name: 'discipline-detail',
          component: DisciplineDetail,
          props: true,
          meta: { title: 'Информация о дисциплине' }
        }
      ]
    },
    {
      path: '/chat',
      name: 'Чат',
      component: ChatPage,
    }
  ],
})

export default router
