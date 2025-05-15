<template>
    <div class="title mt-5">Задание</div>
    <div class="mt-3">{{ work.task }}</div>
    <div class="d-flex align-items-center mt-5 gap-4">
        <div class="title text-nowrap">Номер работы</div>
        <div>{{ work.number }}</div>
    </div>
    <div class="d-flex align-items-center mt-3 gap-4">
        <div class="title">Документ</div>
        <div>{{ work.document }}</div>
    </div>
    <div class="d-flex align-items-center mt-3 gap-4">
        <div class="title">Раздел</div>
        <div>{{ work.document_section }}</div>
    </div>

    <div class="d-flex justify-content-between mt-5">
        <div class="title align-self-end">Студенты</div>
        <button
            class="btn action_button add_student text-white rounded-3 d-flex align-items-center justify-content-center"
            data-bs-toggle="modal" data-bs-target="#addStudentModal">Добавить
        </button>
    </div>

    <table class="table text-nowrap table-hover border-top mt-3">
        <thead class="text-uppercase">
            <tr>
                <th>Фамилия</th>
                <th>Имя</th>
                <th>Статус сдачи работы</th>
                <th class="text-center">Действия</th>
            </tr>
        </thead>
        <tbody>
            <tr v-for="student in assignedStudents" :key="student.id">
                <td>{{ student.last_name }}</td>
                <td>{{ student.first_name }}</td>
                <td>{{ student.status }}</td>
                <td class="text-center">
                    <button class="btn remove_button p-0 m-0" title="Убрать студента из работы"
                        @click="prepareRemoveStudent(student)" data-bs-toggle="modal"
                        data-bs-target="#removeStudentFromWorkModal">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        </tbody>
    </table>
    <div class="d-flex justify-content-end mt-auto">
        <router-link
            class="btn action_button back_button text-white rounded-3 d-flex align-items-center justify-content-center"
            :to="{ name: 'discipline-detail', params: { id: id } }">Назад</router-link>
        <router-link
            class="btn action_button edit_button text-white rounded-3 ms-3 d-flex align-items-center justify-content-center"
            :to="{ name: 'work-edit', params: { id: id, workId: workId } }">Изменить</router-link>
    </div>

    <div class="modal fade" id="addStudentModal" tabindex="-1" aria-labelledby="addStudentModalLabel"
        aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="addStudentModalLabel">
                        Добавить студентов в работу
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="position-relative">
                        <input type="text" class="form-control" placeholder="Поиск по фамилии или логину"
                            v-model="query" @input="onInput" />
                        <ul v-if="showSuggestions && suggestions.length"
                            class="list-group position-absolute w-100 mt-1 zindex-tooltip"
                            style="max-height:200px; overflow-y:auto;">
                            <li v-for="user in suggestions" :key="user.id"
                                class="list-group-item list-group-item-action" @click="selectUser(user)">
                                {{ user.last_name }} {{ user.first_name }}
                                <small class="text-muted ms-2">({{ user.login }})</small>
                            </li>
                        </ul>
                        <div v-if="query.length > 0 && query.length < 2" class="small text-muted mt-1">
                            Введите минимум 2 символа
                        </div>
                    </div>
                    <div class="mt-3">
                        <div v-for="user in selectedUsers" :key="user.id"
                            class="badge selectedStudents me-1 mb-1 align-middle">
                            {{ user.last_name }} {{ user.first_name }}
                            <button type="button" class="btn btn-close btn-close-white btn-sm ms-2" aria-label="Удалить"
                                @click="removeFromSelected(user.id)"></button>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Отмена</button>
                    <button type="button" class="btn btn-primary" :disabled="!selectedUsers.length"
                        @click="addStudentsToWork" data-bs-dismiss="modal">Добавить</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Модальное окно удаления студента из работы -->
    <div class="modal fade" id="removeStudentFromWorkModal" tabindex="-1"
        aria-labelledby="removeStudentFromWorkModalLabel" aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="removeStudentFromWorkModalLabel">Удаление студента из работы</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    Удалить студента
                    <strong>{{ studentToRemove?.last_name }} {{ studentToRemove?.first_name }}</strong>
                    из работы?
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                        Отмена
                    </button>
                    <button type="button" class="btn btn-danger" @click="removeStudentFromWork" data-bs-dismiss="modal">
                        Удалить
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import axios from 'axios';
import debounce from 'lodash.debounce'
import Cookies from 'js-cookie';

interface User {
    id: number
    last_name: string
    first_name: string
    login: string
}

interface Assigned {
    id: number
    last_name: string
    first_name: string
    status: string
}

export default defineComponent({
    name: "WorkDetail",
    props: {
        id: {
            type: Number,
            required: true
        },
        workId: {
            type: Number,
            required: true
        }
    },
    data() {
        return {
            work: {
                name: '',
                task: '',
                number: 0,
                document: '',
                document_section: ''
            },
            // Назанченные в работу в студенты
            assignedStudents: [] as Assigned[],

            // Студенты преподавателя
            teacherStudents: [] as User[],

            query: '',
            suggestions: [] as User[],
            showSuggestions: false,
            selectedUsers: [] as User[],
            studentToRemove: { id: 0, last_name: '', first_name: '' } as { id: number; last_name: string; first_name: string }
        }
    },
    methods: {
        // Получить информацию о работе
        async get_work_info() {
            try {
                const accessToken = Cookies.get('access_token');

                const response = await axios.get(`/api/disciplines/${this.id}/work/${this.workId}`,
                    { headers: { 'Authorization': `Bearer ${accessToken}` } }
                );

                this.work.name = response.data.Work.name;
                this.work.task = response.data.Work.task;
                this.work.number = response.data.Work.number;
                this.work.document = response.data.Work.document_name;
                this.work.document_section = response.data.Work.document_section;

                this.assignedStudents = response.data.Work.students;

                // обновляем заголовок
                this.$emit('set-page-title', response.data.Work.name)

            } catch (error) {
                console.log(error);
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при получении информации о работе:', error);
                }
            }
        },
        // Получить студентов преподавателя
        async fetch_teacher_students() {
            try {
                const access_token = Cookies.get('access_token');

                const response = await axios.get('/api/users/me/students',
                    { headers: { Authorization: `Bearer ${access_token}` } }
                );

                this.teacherStudents = response.data.Students;

            } catch (error) {
                console.log(error);
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при получении студентов преподавателя:', error);
                }
            }
        },
        // Поиск студентов в списке преподавателя для назначения в работу
        onInput() {
            if (this.query.length >= 2) {
                this.showSuggestions = true
                this.debouncedFetch()
            } else {
                this.showSuggestions = false
                this.suggestions = []
            }
        },
        debouncedFetch: debounce(function (this: any) {
            const q = this.query.toLowerCase()
            this.suggestions = this.teacherStudents
                .filter((user: { last_name: string; first_name: string; login: string; }) =>
                    (user.last_name + ' ' + user.first_name).toLowerCase().includes(q) ||
                    user.login.toLowerCase().includes(q)
                )
                .filter((u: { id: number; }) => !this.selectedUsers.find((s: { id: number; }) => s.id === u.id))
        }, 300),
        // Выбрать студентов для назначения в работу
        selectUser(user: User) {
            this.selectedUsers.push(user)
            this.query = ''
            this.showSuggestions = false
        },
        // Удалить студентов из временного списка назначения на работу
        removeFromSelected(id: number) {
            this.selectedUsers = this.selectedUsers.filter(u => u.id !== id)
        },
        // Добавить выбранных студентов в работу
        async addStudentsToWork() {
            try {
                // Если выбранных студентов нет - не добавляем
                if (!this.selectedUsers.length) return

                const access_token = Cookies.get('access_token')

                await axios.post(`/api/disciplines/${this.id}/work/${this.workId}/students/add`,
                    { ids: this.selectedUsers.map(u => u.id) },
                    { headers: { Authorization: `Bearer ${access_token}` } }
                )

                // Обновляем информацию о работе на странице
                this.selectedUsers = []
                await this.get_work_info()

            } catch (error) {
                console.log(error);
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при назначении студента в работу:', error);
                }
            }
        },
        // Подготовка студента для удаления из работы
        prepareRemoveStudent(student: { id: number; last_name: string; first_name: string }) {
            this.studentToRemove = student
        },
        // Удалить студента из списка
        async removeStudentFromWork() {
            try {
                const accessToken = Cookies.get('access_token')

                await axios.delete(`/api/disciplines/${this.id}/work/${this.workId}/students/${this.studentToRemove.id}/remove`,
                    { headers: { Authorization: `Bearer ${accessToken}` } }
                )

                this.assignedStudents = this.assignedStudents.filter(s => s.id !== this.studentToRemove.id)

            } catch (error) {
                console.log(error);
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при удалении студента из работы:', error);
                }
            }
        }
    },
    async mounted() {
        await Promise.all([
            this.get_work_info(),
            this.fetch_teacher_students(),
        ])
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

.back_button {
    background-color: #B7B4B4;
}

.add_student,
.edit_button {
    background-color: #53B1F5;
}

.remove_button {
    font-size: inherit;
}

.zindex-tooltip {
    z-index: 1055
}

.selectedStudents {
    background-color: #d74f37;
}
</style>