<template>
    <transition name="slide-fade">
        <aside v-if="showPanel" class="left_panel pt-3 d-flex flex-column">
            <div class="namelogo d-flex align-items-center justify-content-center px-2">
                <div class="logo"><img class="logo_icon" src="@/assets/neurotutor_logo.svg" alt="Лого" /></div>
                <div class="site_name ms-2 fw-semibold">NeuroTutor</div>
            </div>
            <div class="d-flex align-items-center mt-5 justify-content-center px-2">
                <router-link
                    class="btn add_discipline d-flex justify-content-center align-items-center text-white px-2 py-1 text-nowrap"
                    :to="{ name: 'discipline-new' }" v-if="user?.role === 'teacher'">
                    <img src="@/assets/book.svg" alt="Новый чат" class="book_icon me-2" />
                    <span class="add_discipline_text">Добавить дисциплину</span>
                </router-link>
            </div>
            <div class="disciplines_list_name mt-4 mb-2 ms-3 fw-medium">Список дисциплин</div>
            <div class="disciplines_list border-bottom">
                <div v-for="discipline in disciplines" :key="discipline.id"
                    class="discipline d-flex align-items-center px-3 rounded-2"
                    :class="{ selected_discipline: selectedDisciplineId === discipline.id }"
                    @click="selectDiscipline(discipline.id)">
                    <span class="d-block text-truncate">{{ discipline.name }}</span>
                </div>
            </div>

            <div class="d-flex flex-column align-items-center my-4 gap-2 px-2">
                <router-link
                    class="btn students_button text-white d-flex align-items-center justify-content-center rounded-3"
                    :to="{ name: 'students' }" v-if="user?.role === 'teacher'">Студенты</router-link>
                <!-- Кнопка профиля со всплывающей информацией о пользователе -->
                <ProfileButton />
            </div>
        </aside>
    </transition>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import axios from 'axios';
import ProfileButton from '@/components/ui/ProfileButton.vue';
import Cookies from 'js-cookie';
import { useAuthStore } from '@/stores/auth'

export default defineComponent({
    name: 'LeftPanel',
    components: {
        ProfileButton
    },
    props: {
        showPanel: {
            type: Boolean,
            default: false
        }
    },
    computed: {
        user() {
            return useAuthStore().user
        }
    },
    data() {
        return {
            disciplines: [] as Array<{ id: number; name: string }>,
            selectedDisciplineId: undefined as number | undefined
        }
    },
    methods: {
        // Получить все дисциплины текущего преподавателя
        async get_disciplines() {
            try {
                const accessToken = Cookies.get('access_token');

                const response = await axios.get(`/api/users/me/disciplines`,
                    { headers: { 'Authorization': `Bearer ${accessToken}` } }
                );

                this.disciplines = response.data.Disciplines.reverse();

            } catch (error) {
                console.log(error);
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при получении дисциплин:', error);
                }
            }
        },
        // Выбрать дисциплину
        async selectDiscipline(id: number) {
            // Если уже именно на странице discipline-detail c этим id — ничего не делаем
            if (this.$route.name === 'discipline-detail' && Number(this.$route.params.id) === id) return;
            // Иначе — всегда переходим на detail нужной дисциплины
            this.$router.push({ name: 'discipline-detail', params: { id } });
        },
        /** подсветка активной дисциплины по URL */
        syncSelectedFromRoute() {
            const id = Number(this.$route.params.id)
            this.selectedDisciplineId = Number.isFinite(id) ? id : undefined
        },
        // Обновить название дисциплины (вызывается из DisciplineDetail.vue)
        updateDisciplineName(id: number, name: string) {
            const d = this.disciplines.find(d => d.id === id)
            if (d) { d.name = name }
        }
    },
    async mounted() {
        await this.get_disciplines()
        this.syncSelectedFromRoute()
    },
    watch: {
        /* реагируем на любое изменение маршрута */
        $route() {
            this.syncSelectedFromRoute()
            if (this.$route.path.startsWith('/disciplines')) {
                this.get_disciplines()
            }
        }
    },
})
</script>

<style scoped>
.logo_icon {
    max-width: 66px;
    width: 100%;
}

.site_name {
    font-size: 2rem;
}

.book_icon {
    max-width: 2rem;
    width: 100%;
}

.add_discipline {
    background-color: #d74f37;
    max-width: 311px;
    width: 100%;
    font-size: inherit;
}

.discipline {
    height: 33px;
    cursor: pointer;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
}

/* Выбор дисциплины */
.selected_discipline {
    background-color: #D9D9D9;
}

/* Левая панель */
.left_panel {
    background-color: #efefef;
    height: 100vh;
    position: fixed;
    top: 0;
    left: 0;
    width: 16.666666%;
}

/* Анимация появления и исчезновения левой панели */
.slide-fade-enter-active,
.slide-fade-leave-active {
    transition: all 0.3s ease;
}

.slide-fade-enter-from,
.slide-fade-leave-to {
    transform: translateX(-100%);
    opacity: 0;
}

.slide-fade-enter-to,
.slide-fade-leave-from {
    transform: translateX(0);
    opacity: 1;
}

.students_button {
    background-color: #53B1F5;
    max-width: 247px;
    width: 100%;
    height: 42px;
    font-size: inherit;
}

@media (max-width: 1750px) {
    .add_discipline {
        font-size: 1rem;
    }
}

/* Скролл списка дисциплин */
.disciplines_list {
  flex: 1 1 auto;        /* занимает всё оставшееся место */
  overflow-y: auto;      /* добавляет вертикальную полосу прокрутки */
}
.discipline {
  box-sizing: border-box;
}
.text-truncate {
  display: block;
  width: 100%;
  box-sizing: border-box;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
</style>