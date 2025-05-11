<template>
    <div class="title mb-2 mt-5">Назовите дисциплину</div>
    <input type="text" class="discipline_name form-control rounded-3" v-model="title">
    <div class="title mb-2 mt-5">Загрузите документы</div>
    <input ref="fileInput" type="file" multiple class="add_documents" @change="handleFiles">
    <div class="title mb-2 mt-5">Загруженные документы</div>
    <div class="files d-flex gap-4 flex-wrap">
        <div v-for="(file, i) in files" :key="file.name + i" class="d-flex flex-column align-items-center file-item">
            <img src="@/assets/file_icon.svg" alt="Файл" width="100" />
            <small class="text-center mt-1">{{ truncateString(file.name, 22) }}</small>
            <button class="btn btn-link p-0 mt-1" @click="removeFile(i)">
                Удалить файл
            </button>
        </div>
    </div>

    <div class="d-flex justify-content-end mt-auto">
        <router-link class="btn cancel_button text-white rounded-3 d-flex align-items-center justify-content-center"
            :to="{ name: 'blank-area' }">Отмена</router-link>
        <button class="btn add_button text-white rounded-3 ms-3 d-flex align-items-center justify-content-center"
            :disabled="!canSubmit" @click="add_discipline">Добавить</button>
    </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import axios from 'axios';

export default defineComponent({
    name: 'DisciplineCreate',
    data() {
        return {
            title: '',
            files: [] as File[]
        }
    },
    computed: {
        canSubmit(): boolean {
            return this.title.trim().length > 0 && this.files.length > 0
        }
    },
    methods: {
        handleFiles(e: Event) {
            const input = e.target as HTMLInputElement
            if (input.files) this.files.push(...Array.from(input.files))
            input.value = '' // чтоб можно было выбрать тот же файл ещё раз
        },
        removeFile(idx: number) {
            this.files.splice(idx, 1)
        },
        // Обрезка строки в соответствии с количеством символов
        truncateString(str: string, num: number): string {
            return str.length > num ? str.slice(0, num) + "..." : str;
        },
        // Добавление дисциплины
        async add_discipline() {
            if (!this.canSubmit) return

            try {
                const accessToken = this.getCookie('access_token');

                /* 1. конвертируем каждый File в base64, т.к. FastAPI ждёт bytes */
                const docs = await Promise.all(
                    this.files.map(file => new Promise<{ name: string; data: string }>((resolve, reject) => {
                        const reader = new FileReader()
                        reader.onload = () => {
                            const base64 = (reader.result as string).split(',')[1] // обрезаем "data:...;base64,"
                            resolve({ name: file.name, data: base64 })
                        }
                        reader.onerror = reject
                        reader.readAsDataURL(file)
                    }))
                )

                /* 2. собираем DTO один-в-один как на сервере */
                const new_discipline = {
                    name: this.title.trim(),
                    documents: docs
                }

                /* 3. Отправляем запрос */
                const response = await axios.post(`/api/users/me/disciplines/add`,
                    new_discipline,
                    { headers: { 'Authorization': `Bearer ${accessToken}` } }
                );

                /* 4. успех → вернуться к списку */
                this.$router.push('/disciplines')

                const id = response.data.id
                this.$router.push({ name: 'discipline-detail', params: { id } })

            } catch (error) {
                console.log(error);
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при добавлении дисциплины:', error);
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
    }
})
</script>

<style scoped>
.title {
    font-size: 24px;
}

.cancel_button {
    background-color: #F45D5D;
    width: 190px;
    height: 40px;
    font-size: inherit;
}

.add_button {
    background-color: #53B1F5;
    width: 190px;
    height: 40px;
    font-size: inherit;
}
</style>