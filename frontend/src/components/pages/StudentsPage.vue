<template>
    <div class="container-fluid">
        <!-- Левая панель -->
        <LeftPanel ref="leftPanel" :showPanel="showPanel" :getCookie="getCookie" />

        <!-- Основная область -->
        <MainPanel :showPanel="showPanel" :pageTitle="pageTitle" @togglePanel="togglePanel">
            <div class="d-flex justify-content-between mt-5">
                <div class="title align-self-end">Студенты</div>
                <button
                    class="btn action_button add_student text-white rounded-3 d-flex align-items-center justify-content-center"
                    data-bs-toggle="modal" data-bs-target="#addStudentModalToList">Добавить
                </button>
            </div>

            <table class="table text-nowrap table-hover border-top mt-3">
                <thead class="text-uppercase">
                    <tr>
                        <th>Фамилия</th>
                        <th>Имя</th>
                        <th>Логин</th>
                        <th class="text-center">Действия</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="student in students" :key="student.id">
                        <td>{{ student.last_name }}</td>
                        <td>{{ student.first_name }}</td>
                        <td>{{ student.login }}</td>
                        <td class="text-center">
                            <button class="btn remove_button p-0 m-0" title="Удалить студента"
                                @click="prepareRemoveStudent(student)" data-bs-toggle="modal"
                                data-bs-target="#removeStudentFromListModal">
                                <i class="bi bi-trash"></i>
                            </button>
                        </td>
                    </tr>
                </tbody>
            </table>

            <div class="modal fade" id="addStudentModalToList" tabindex="-1"
                aria-labelledby="addStudentModalToListLabel" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="addStudentModalToListLabel">Добавить студента</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="position-relative">
                                <!-- Поисковая строка -->
                                <input type="text" class="form-control" placeholder="Введите фамилию или логин"
                                    v-model="query" @input="onInput" />

                                <!-- Список подсказок -->
                                <ul v-if="showSuggestions && suggestions.length"
                                    class="list-group position-absolute w-100 mt-1 zindex-tooltip"
                                    style="max-height:200px; overflow-y:auto;">
                                    <li v-for="user in suggestions" :key="user.id"
                                        class="list-group-item list-group-item-action" @click="selectUser(user)">
                                        <div>{{ user.last_name }} {{ user.first_name }}</div>
                                        <small class="text-muted">{{ user.login }}</small>
                                    </li>
                                </ul>

                                <!-- Сообщение про минимум 2 символа -->
                                <div v-if="query.length > 0 && query.length < 2" class="small text-muted mt-1">
                                    Введите минимум 2 символа для начала поиска
                                </div>

                                <!-- Выбранные участники -->
                                <div class="mt-3">
                                    <div v-for="u in selectedUsers" :key="u.id"
                                        class="badge selectedUsers me-1 mb-1 align-middle">
                                        {{ u.last_name }} {{ u.first_name }}
                                        <button type="button" class="btn btn-close btn-close-white btn-sm ms-2"
                                            @click="removeFromSelected(u.id)"></button>
                                    </div>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                    Отмена
                                </button>
                                <button type="button" class="btn btn-primary" :disabled="selectedUsers.length === 0"
                                    @click="addUsersToList" data-bs-dismiss="modal">
                                    Добавить
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Модальное окно удаления студента из списка преподавателя -->
            <div class="modal fade" id="removeStudentFromListModal" tabindex="-1" aria-labelledby="removeStudentFromListModalLabel"
                aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="removeStudentFromListModalLabel">Удаление студента</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            Удалить студента
                            <strong>{{ studentToRemove?.last_name }} {{ studentToRemove?.first_name }}</strong>
                            из списка преподавателя?
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                Отмена
                            </button>
                            <button type="button" class="btn btn-danger" @click="removeStudent" data-bs-dismiss="modal">
                                Удалить
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </MainPanel>
    </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import axios from 'axios'
import debounce from 'lodash.debounce'
import LeftPanel from '@/components/ui/LeftPanel.vue';
import MainPanel from '@/components/ui/MainPanel.vue';

interface User {
    id: number
    last_name: string
    first_name: string
    login: string
}

export default defineComponent({
    name: 'StudentsPage',
    components: {
        LeftPanel,
        MainPanel
    },
    data() {
        return {
            showPanel: true,

            // текущие студенты (уже добавленные)
            students: [] as User[],

            // Строка-запрос на поиск пользователей
            query: '',
            suggestions: [] as User[],
            showSuggestions: false,
            selectedUsers: [] as User[],
            studentToRemove: { id: 0, last_name: '', first_name: '' } as { id: number; last_name: string; first_name: string }
        }
    },
    computed: {
        // берём заголовок из meta текущего маршрута
        pageTitle(): string {
            return String(this.$route.meta.title ?? '')
        }
    },
    methods: {
        // Получить куки для name
        getCookie(name: string) {
            let matches = document.cookie.match(new RegExp(
                "(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') + "=([^;]*)"
            ));
            return matches ? decodeURIComponent(matches[1]) : undefined;
        },
        /* переключение боковой панели */
        togglePanel() {
            this.showPanel = !this.showPanel
        },
        // Получить всех студентов преподавателя
        async fetchStudents() {
            try {
                const accessToken = this.getCookie('access_token');

                const response = await axios.get('/api/users/me/students',
                    { headers: { Authorization: `Bearer ${accessToken}` } }
                );

                this.students = response.data.Students;

            } catch (error) {
                console.log(error);
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при получении студентов преподавателя:', error);
                }
            }
        },
        // Подготовка студента для удаления из списка
        prepareRemoveStudent(student: { id: number; last_name: string; first_name: string }) {
            this.studentToRemove = student
        },
        // Удалить студента из списка
        async removeStudent() {
            try {
                const accessToken = this.getCookie('access_token')

                await axios.delete(`/api/users/me/student/${this.studentToRemove.id}/remove`,
                    { headers: { Authorization: `Bearer ${accessToken}` } }
                )

                this.students = this.students.filter(s => s.id !== this.studentToRemove.id)

            } catch (error) {
                console.log(error);
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при удалении студента из списка преподавателя:', error);
                }
            }
        },

        // — ПОИСК И ВЫБОР В МОДАЛКЕ —
        onInput() {
            if (this.query.length >= 2) {
                this.showSuggestions = true
                this.debouncedFetch()
            } else {
                this.showSuggestions = false
                this.suggestions = []
            }
        },

        // Получить студентов в поиске для добавления в список преподавателя
        debouncedFetch: debounce(async function (this: any) {
            try {
                const token = this.getCookie('access_token')

                const response = await axios.get(
                    `/api/users/search?query=${encodeURIComponent(this.query)}`,
                    { headers: { Authorization: `Bearer ${token}` } }
                )

                // убираем уже избранных
                this.suggestions = response.data.Users.filter((u: { id: number; }) => !this.selectedUsers.find((s: { id: number; }) => s.id === u.id))

            } catch (error) {
                console.log(error);
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при поиске пользователей:', error);
                }
            }
        }, 300),

        // Выбрать пользователя для добавления в список
        selectUser(user: User) {
            this.selectedUsers.push(user)
            this.query = ''
            this.showSuggestions = false
        },

        // Удалить пользователя из списка выбора на добавления
        removeFromSelected(id: number) {
            this.selectedUsers = this.selectedUsers.filter(u => u.id !== id)
        },

        // Добавить студентов в список преподавателя
        async addUsersToList() {
            // Если выбранных пользователей нет - не добавляем
            if (!this.selectedUsers.length) return

            try {
                const access_token = this.getCookie('access_token')

                await axios.post('/api/users/me/students/add',
                    { ids: this.selectedUsers.map(u => u.id) },
                    { headers: { Authorization: `Bearer ${access_token}` } }
                )

                // обновляем список
                await this.fetchStudents()
                this.selectedUsers = []

            } catch (error) {
                console.log(error);
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при добавлении студентов в список преподавтеля:', error);
                }
            }
        },
    },
    mounted() {
        this.fetchStudents()
    }
})
</script>

<style scoped>
.title {
    font-size: 24px;
}

.action_button {
    font-size: inherit;
    width: 190px;
    height: 40px;
}

.remove_button {
    font-size: inherit;
}

.add_student {
    background-color: #53B1F5;
}

.zindex-tooltip {
    z-index: 1055
}

.selectedUsers {
    background-color: #d74f37;
}
</style>