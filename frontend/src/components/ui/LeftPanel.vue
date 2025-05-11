<template>
    <transition name="slide-fade">
        <div v-if="showPanel" class="left_panel pt-3 d-flex flex-column">
            <div class="namelogo d-flex align-items-center justify-content-center">
                <div class="logo"><img src="@/assets/neurotutor_logo.svg" alt="Лого" width="66" /></div>
                <div class="site_name ms-2 fw-semibold">NeuroTutor</div>
            </div>
            <div class="d-flex align-items-center mt-5 justify-content-center">
                <button class="btn add_discipline d-flex justify-content-center align-items-center text-white"
                    @click="add_discipline">
                    <img src="@/assets/book.svg" alt="Новый чат" width="34" class="me-2" />Добавить дисциплину
                </button>
            </div>
            <div class="disciplines_list_name mt-4 mb-2 ms-3 fw-medium">Список дисциплин</div>
            <div class="disciplines_list">
                <div v-for="discipline in disciplines" :key="discipline.id"
                    class="discipline d-flex align-items-center px-3 rounded-2"
                    :class="{ selected_discipline: selectedDisciplineId === discipline.id }"
                    @click="selectedDiscipline(discipline.id)">
                    {{ truncateString(discipline.name, 30) }}
                </div>
            </div>

            <!-- Кнопка профиля со всплывающей информацией о пользователе -->
            <ProfileButton :getCookie="getCookie" />
        </div>
    </transition>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import axios from 'axios';
import ProfileButton from '@/components/ui/ProfileButton.vue';

export default defineComponent({
    name: 'LeftPanel',
    components: {
        ProfileButton
    },
    props: {
        showPanel: {
            type: Boolean,
            default: false
        },
        getCookie: {
            type: Function,
            required: true
        }
    },
    data() {
        return {
            disciplines: [] as Array<{ id: number; name: string }>,
            selectedDisciplineId: undefined as number | undefined
        }
    },
    methods: {
        // Добавление дисциплины
        async add_discipline() {
            try {
                const accessToken = this.getCookie('access_token');

                const response = await axios.post(`/api/users/me/disciplines/add`,
                    {},
                    { headers: { 'Authorization': `Bearer ${accessToken}` } }
                );

                this.get_disciplines()
                this.selectedDisciplineId = response.data.newChatSessionId;

            } catch (error) {
                console.log(error);
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при добавлении чата:', error);
                }
            }
        },
        // Получить все дисциплины текущего преподавателя
        async get_disciplines() {
            try {
                const accessToken = this.getCookie('access_token');

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
        async selectedDiscipline(disciplineId: number) {
            if (this.selectedDisciplineId === disciplineId) return // повторный клик – ничего не делаем
            this.selectedDisciplineId = disciplineId
        },
        // Обрезка строки в соответствии с количеством символов
        truncateString(str: string, num: number): string {
            return str.length > num ? str.slice(0, num) + "..." : str;
        },
    },
    mounted() {
        this.get_disciplines();
    },
})
</script>

<style scoped>
.site_name {
    font-size: 36px
}

.add_discipline {
    background-color: #d74f37;
    width: 311px;
    height: 42px;
    font-size: inherit;
}

.discipline {
    height: 33px;
    cursor: pointer;
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
</style>