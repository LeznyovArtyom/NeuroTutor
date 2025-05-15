<template>
    <div class="title mt-5">Задание</div>
    <div class="mt-3">
        {{ work.task }}
    </div>
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
                <th>Действия</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Егорова</td>
                <td>София</td>
                <td>Принята</td>
                <td><i class="bi bi-trash"></i></td>
            </tr>
            <tr>
                <td>Волков</td>
                <td>Михаил</td>
                <td>На доработке</td>
                <td><i class="bi bi-trash"></i></td>
            </tr>
        </tbody>
    </table>
    <div class="d-flex justify-content-end mt-auto">
        <router-link
            class="btn action_button back_button text-white rounded-3 d-flex align-items-center justify-content-center"
            :to="{ name: 'discipline-detail', params: { id: id } }">Назад</router-link>
        <router-link
            class="btn action_button edit_button text-white rounded-3 ms-3 d-flex align-items-center justify-content-center"
            :to="{ name: 'work-edit', params: { id: id, workId: work.id } }">Изменить</router-link>
    </div>

    <div class="modal fade" id="addStudentModal" tabindex="-1" aria-labelledby="addStudentModalLabel"
        aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="addStudentModalLabel">Добавить студента</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div>Выберите из списка</div>
                    <select class="form-select my-2">
                        <option value="">София</option>
                        <option value="">Михаил</option>
                    </select>

                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                        Отмена
                    </button>
                    <button type="button" class="btn btn-primary" data-bs-dismiss="modal">
                        Добавить
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import axios from 'axios';

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
        }
    },
    methods: {
        async get_work_info() {
            try {
                const accessToken = this.getCookie('access_token');

                const response = await axios.get(`/api/disciplines/${this.id}/work/${this.workId}`,
                    { headers: { 'Authorization': `Bearer ${accessToken}` } }
                );

                this.work.name = response.data.Work.name;
                this.work.task = response.data.Work.task;
                this.work.number = response.data.Work.number;
                this.work.document = response.data.Work.document_name;
                this.work.document_section = response.data.Work.document_section;

            } catch (error) {
                console.log(error);
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при получении информации о работе:', error);
                }
            }
        },
        // Получить куки для name
        getCookie(name: string) {
            let matches = document.cookie.match(new RegExp(
                "(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') + "=([^;]*)"
            ));
            return matches ? decodeURIComponent(matches[1]) : undefined;
        },
    },
    mounted() {
        this.get_work_info();
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
</style>