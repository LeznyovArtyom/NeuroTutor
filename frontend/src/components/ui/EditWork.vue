<template>
    <div class="title mt-5">Название работы</div>
    <input class="form-control mt-3" v-model="work.name" />
    <div class="title mt-5">Задание</div>
    <textarea class="form-control mt-3" rows="20" v-model="work.task"></textarea>
    <div class="d-flex mt-5 gap-4">
        <div class="title text-nowrap">Номер работы</div>
        <select class="form-select w-auto" v-model="work.number">
            <option v-for="number in Array.from({ length: workCount }, (_, i) => i + 1)" :value="number">{{ number }}
            </option>
        </select>
    </div>
    <div class="d-flex justify-content-between mt-5">
        <div class="document_container me-3">
            <div class="title">Документ</div>
            <select class="form-select select_document mt-3" v-model="work.document_id">
                <option value=""></option>
                <option v-for="document in documents" :value="document.id" :key="document.id">{{ document.name }}
                </option>
            </select>
        </div>
        <div class="section_container">
            <div class="title">Раздел</div>
            <input type="text" class="form-control section_input mt-3" v-model="work.document_section">
        </div>
    </div>
    <div class="d-flex justify-content-end mt-auto">
        <router-link
            class="btn action_button cancel_button text-white rounded-3 d-flex align-items-center justify-content-center"
            :to="{ name: 'discipline-detail', params: { id: id } }">Отмена</router-link>
        <button
            class="btn action_button edit_button text-white rounded-3 ms-3 d-flex align-items-center justify-content-center"
            :disabled="!canSubmit" @click="edit_work">Изменить</button>
    </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import axios from 'axios';
import Cookies from 'js-cookie';

export default defineComponent({
    name: "EditWork",
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
                document_id: '',
                document_section: ''
            },
            originalWork: {
                name: '',
                task: '',
                number: 0,
                document_id: '',
                document_section: ''
            },
            documents: [] as Array<{ id: number; name: string }>,
            workCount: 0
        }
    },
    computed: {
        canSubmit(): boolean {
            return this.work.name.trim().length > 0 && this.work.task.trim().length > 0 && this.work.number > 0 && this.work.document_id !== '' && this.work.document_section.trim().length > 0;
        }
    },
    methods: {
        async get_work_info() {
            try {
                const accessToken = Cookies.get('access_token');

                const response = await axios.get(`/api/disciplines/${this.id}/work/${this.workId}`,
                    { headers: { 'Authorization': `Bearer ${accessToken}` } }
                );

                this.work.name = response.data.Work.name;
                this.work.task = response.data.Work.task;
                this.work.number = response.data.Work.number;
                this.work.document_id = response.data.Work.document_id;
                this.work.document_section = response.data.Work.document_section;

                this.originalWork = Object.assign({}, this.work);

            } catch (error) {
                console.log(error);
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при получении информации о работе:', error);
                }
            }
        },
        // Получить информацию о дисциплине
        async get_discipline_info() {
            try {
                const accessToken = Cookies.get('access_token');

                const response = await axios.get(`/api/users/me/disciplines/${this.id}`,
                    { headers: { 'Authorization': `Bearer ${accessToken}` } }
                );

                this.documents = response.data.Discipline.documents;
                this.workCount = response.data.Discipline.works.length;

            } catch (error) {
                console.log(error);
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при получении дисциплины:', error);
                }
            }
        },
        async edit_work() {
            try {
                const accessToken = Cookies.get('access_token');

                const updatedFields: { name?: string, task?: string, number?: number, document_id?: number, document_section?: string } = {};
                if (this.originalWork.name !== this.work.name) {
                    updatedFields.name = this.work.name.trim();
                }
                if (this.originalWork.task !== this.work.task) {
                    updatedFields.task = this.work.task.trim();
                }
                if (this.originalWork.number !== this.work.number) {
                    updatedFields.number = Number(this.work.number);
                }
                if (this.originalWork.document_id !== this.work.document_id) {
                    updatedFields.document_id = Number(this.work.document_id);
                }
                if (this.originalWork.document_section !== this.work.document_section) {
                    updatedFields.document_section = this.work.document_section.trim();
                }

                if (Object.keys(updatedFields).length === 0) {
                    alert('Нет изменений для сохранения.');
                    return;
                }

                await axios.put(`/api/disciplines/${this.id}/work/${this.workId}/update`,
                    updatedFields,
                    { headers: { Authorization: `Bearer ${accessToken}` } }
                );

                this.$router.push({ name: 'discipline-detail', params: { id: this.id } });
            } catch (error) {
                console.log(error);
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при изменении информации о работе:', error);
                }
            }
        }
    },
    mounted() {
        this.get_work_info();
        this.get_discipline_info();
    }
})
</script>

<style scoped>
.title {
    font-size: 24px;
}

.document_container {
    max-width: 350px;
    width: 100%;
}

.section_container {
    max-width: 700px;
    width: 100%;
}

.action_button {
    width: 190px;
    height: 40px;
    font-size: inherit;
}

.cancel_button {
    background-color: #F45D5D;
}

.edit_button {
    background-color: #53B1F5;
}
</style>