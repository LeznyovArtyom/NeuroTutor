import { createRouter, createWebHistory } from 'vue-router'
import ChatPage from '@/components/pages/ChatPage.vue'
import IndexPage from '@/components/pages/IndexPage.vue'
import AuthorizationPage from '@/components/pages/AuthorizationPage.vue'
import RegistrationPage from '@/components/pages/RegistrationPage.vue'
import DisciplinesLayoutPage from '@/components/pages/DisciplinesLayoutPage.vue'
import BlankArea from '@/components/ui/BlankArea.vue'
import DisciplineCreate from '@/components/ui/DisciplineCreate.vue'
import DisciplineDetail from '@/components/ui/DisciplineDetail.vue'
import AddWork from '@/components/ui/AddWork.vue'
import EditWork from '@/components/ui/EditWork.vue'
import WorkDetail from '@/components/ui/WorkDetail.vue'
import StudentsPage from '@/components/pages/StudentsPage.vue'

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
          props: route => ({ id: Number(route.params.id) }),
          meta: { title: 'Информация о дисциплине' }
        },
        {
          path : ':id(\\d+)/add-work',
          name : 'work-add',
          component: AddWork,
          props: route => ({ id: Number(route.params.id) }),
          meta : { title:'Добавить новую работу' }
        },
        {
          path : ':id(\\d+)/work/:workId(\\d+)',
          name : 'work-detail',
          component: WorkDetail,
          props: route => ({ 
            id: Number(route.params.id),
            workId: Number(route.params.workId),
          }),
          meta : { title:'Информация о работе' }
        },
        {
          path : ':id(\\d+)/work/:workId(\\d+)/edit',
          name : 'work-edit',
          component: EditWork,
          props: route => ({ 
            id: Number(route.params.id),
            workId: Number(route.params.workId),
          }),
          meta : { title:'Изменить информацию о работе' }
        }
      ]
    },
    {
      path: '/students',
      name: 'students',
      component: StudentsPage,
      meta: { title: 'Список студентов' }
    },
    {
      path: '/chat',
      name: 'Чат',
      component: ChatPage,
    }
  ],
})

export default router
