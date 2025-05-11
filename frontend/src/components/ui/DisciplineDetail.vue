<template>
    <div class="d-flex justify-content-between mb-2 mt-5">
        <div class="title">Дисциплина</div>
        <button v-if="!isEditing"
            class="btn change_discipline_name text-white rounded-3 d-flex align-items-center justify-content-center"
            @click="change_discipline_name">Изменить
        </button>
        <div v-else class="d-flex">
            <button class="btn cancel_change text-white rounded-3 d-flex align-items-center justify-content-center" @click="change_discipline_name">Отмена</button>
            <button class="btn save_change text-white rounded-3 ms-3 d-flex align-items-center justify-content-center" @click="saveDisciplineName">Сохранить</button>
        </div>
    </div>
    <div v-if="!isEditing" class="mt-3">{{ discipline.name }}</div>
    <input v-else class="form-control mt-3" v-model="newDiscipline.name" />
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import axios from 'axios';

export default defineComponent({
    name: 'DisciplineDetail',
    props: {
        id: {
            type: Number,
            required: true
        }
    },
    data() {
        return {
            discipline: {
                name: ''
            },
            newDiscipline: {
                name: ''
            },
            isEditing: false,
        }
    },
    emits: ['discipline-renamed'],
    methods: {
        // Получить информацию о дисциплине
        async get_discipline_info() {
            try {
                const accessToken = this.getCookie('access_token');

                const response = await axios.get(`/api/users/me/disciplines/${this.id}`,
                    { headers: { 'Authorization': `Bearer ${accessToken}` } }
                );
                
                this.discipline.name = response.data.Discipline.name;
                this.newDiscipline.name = this.discipline.name;

            } catch (error) {
                console.log(error);
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при получении дисциплин:', error);
                }
            }
        },
        change_discipline_name() {
            this.isEditing = !this.isEditing;
            if (!this.isEditing) {
                this.newDiscipline.name = this.discipline.name;
            }
        },
        // Сохранение нового названия дисциплины
        async saveDisciplineName() {
            const newName = this.newDiscipline.name.trim()
            if (newName === this.discipline.name) {
                this.isEditing = false;
                return;
            }

            try {
                const token = this.getCookie('access_token')
                await axios.put(`/api/users/me/disciplines/${this.id}/update`, 
                    { name: newName },
                    { headers: { Authorization: `Bearer ${token}` } }
                );

                this.discipline.name = newName;
                this.isEditing = false;

                this.$emit('discipline-renamed', { id: this.id, name: newName })
            } catch (error) {
                console.log(error);
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при изменении чата:', error);
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
    created() {
        /* первая загрузка при открытии */
        this.get_discipline_info()
    },
    watch: {
        /* вызываем при каждом изменении :id (переход на другую дисциплину) */
        id() {
            this.get_discipline_info()
        }
    },
})
</script>

<style scoped>
.title {
    font-size: 24px;
}

.change_discipline_name, .save_change {
    background-color: #53B1F5;
}
.cancel_change {
    background-color: #F45D5D;
}
.btn {
    font-size: inherit;
    width: 190px;
    height: 40px;
}
</style>