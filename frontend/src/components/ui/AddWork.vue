<template>
    <div class="title mt-5">Название работы</div>
    <input class="form-control mt-3" v-model="work.name" />
    <div class="title mt-5">Задание</div>
    <textarea class="form-control mt-3" rows="20" v-model="work.task"></textarea>
    <div class="d-flex mt-5 gap-4">
        <div class="title text-nowrap">Номер работы</div>
        <select class="form-select w-auto" v-model="work.number">
            <option v-for="number in Array.from({ length: work.number }, (_, i) => i + 1)" :value="number">{{ number }}</option>
        </select>
    </div>
    <div class="d-flex justify-content-between mt-5">
        <div>
            <div class="title">Документ</div>
            <select class="form-select select_document mt-3" v-model="work.document_id">
                <option value=""></option>
                <option v-for="document in documents" :value="document.id" :key="document.id">{{ document.name }}</option>
            </select>
        </div>
        <div>
            <div class="title">Раздел</div>
            <input type="text" class="form-control section_input mt-3" v-model="work.document_section">
        </div>
    </div>
    <div class="d-flex justify-content-end mt-auto">
        <router-link
            class="btn action_button cancel_button text-white rounded-3 d-flex align-items-center justify-content-center"
            :to="{ name: 'discipline-detail', params: { id } }">Отмена</router-link>
        <button
            class="btn action_button add_button text-white rounded-3 ms-3 d-flex align-items-center justify-content-center"
            :disabled="!canSubmit" @click="add_work">Добавить</button>
    </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import axios from 'axios';

export default defineComponent({
    name: "AddWork",
    props: {
        id: {
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
            documents: [] as Array<{ id: number; name: string }>,
            work_counter: 0
        }
    },
    computed: {
        canSubmit(): boolean {
            return this.work.name.trim().length > 0 && this.work.task.trim().length > 0 && this.work.document_id !== '' && this.work.document_section.trim().length > 0;
        }
    },
    methods: {
        async add_work() {
            if (!this.canSubmit) return

            try {
                const accessToken = this.getCookie('access_token');

                const new_work = {
                    name: this.work.name,
                    task: this.work.task,
                    number: this.work.number,
                    document_id: this.work.document_id,
                    document_section: this.work.document_section
                }

                await axios.post(`/api/disciplines/${this.id}/work/add`,
                    new_work,
                    { headers: { 'Authorization': `Bearer ${accessToken}` } }
                );

                this.$router.push({ name: 'discipline-detail', params: { id: this.id } });

            } catch (error) {
                console.log(error);
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при добавлении работы в дисциплину:', error);
                }
            }
        },
        // Получить информацию о дисциплине
        async get_discipline_info() {
            try {
                const accessToken = this.getCookie('access_token');

                const response = await axios.get(`/api/users/me/disciplines/${this.id}`,
                    { headers: { 'Authorization': `Bearer ${accessToken}` } }
                );

                this.documents = response.data.Discipline.documents;
                this.work.number = response.data.Discipline.works.length + 1;

            } catch (error) {
                console.log(error);
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при получении дисциплин:', error);
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
        this.get_discipline_info();
    }
})
</script>

<style scoped>
.title {
    font-size: 24px;
}

.select_document {
    width: 350px;
}

.section_input {
    width: 700px;
}

.action_button {
    width: 190px;
    height: 40px;
    font-size: inherit;
}

.cancel_button {
    background-color: #F45D5D;
}

.add_button {
    background-color: #53B1F5;
}
</style>