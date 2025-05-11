<template>
    <div class="title mb-2 mt-5">Дисциплина</div>
    <div>{{ discipline.name }}</div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import axios from 'axios';

export default defineComponent({
    name: 'DisciplineDetail',
    props: { 
        id: { 
            type: String, 
            required: true 
        } 
    },
    data() {
        return {
            discipline: {
                name: ''
            }
        }
    },
    methods: {
        // Получить информацию о дисциплине
        async get_discipline_info() {
            try {
                const accessToken = this.getCookie('access_token');

                const response = await axios.get(`/api/users/me/disciplines/${this.id}`,
                    { headers: { 'Authorization': `Bearer ${accessToken}` } }
                );
                console.log(response.data.Discipline.name);
                this.discipline.name = response.data.Discipline.name;

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
        this.get_discipline_info()
    }
})
</script>

<style>
.title {
    font-size: 24px;
}
</style>