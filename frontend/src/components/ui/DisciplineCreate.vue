<template>
    <div class="title mb-3 mt-5">Назовите дисциплину</div>
    <input type="text" class="discipline_name form-control rounded-3" v-model="title">
    <div class="title mb-3 mt-5">Загрузите документы</div>
    <input type="file" multiple class="add_documents form-control" @change="handleFiles">
    <div class="title mb-3 mt-5">Загруженные документы</div>
    <div class="documents d-flex gap-4 documents-scroll">
        <div v-for="(document, i) in documents" :key="document.name + i"
            class="d-flex flex-column align-items-center file-item">
            <img src="@/assets/file_icon.svg" alt="Файл" width="100" />
            <small class="text-center mt-1">{{ truncateString(document.name, 22) }}</small>
            <button class="btn delete_file btn-link p-0 mt-1" @click="removeFile(i)">
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
import Cookies from 'js-cookie';

export default defineComponent({
    name: 'DisciplineCreate',
    data() {
        return {
            title: '',
            documents: [] as File[]
        }
    },
    computed: {
        canSubmit(): boolean {
            return this.title.trim().length > 0
        }
    },
    methods: {
        handleFiles(e: Event) {
            const input = e.target as HTMLInputElement
            if (input.files) this.documents.push(...Array.from(input.files))
            input.value = '' // чтоб можно было выбрать тот же файл ещё раз
        },
        removeFile(idx: number) {
            this.documents.splice(idx, 1)
        },
        // Обрезка строки в соответствии с количеством символов
        truncateString(str: string, num: number): string {
            return str.length > num ? str.slice(0, num) + "..." : str;
        },
        // Добавление дисциплины
        async add_discipline() {
            if (!this.canSubmit) return

            try {
                const accessToken = Cookies.get('access_token');

                /* 1. конвертируем каждый File в base64, т.к. FastAPI ждёт bytes */
                const docs = await Promise.all(
                    this.documents.map(file => new Promise<{ name: string; data: string }>((resolve, reject) => {
                        const reader = new FileReader()
                        reader.onload = () => {
                            const base64 = (reader.result as string).split(',')[1] // обрезаем "data:...;base64,"
                            resolve({ name: file.name, data: base64 })
                        }
                        reader.onerror = reject
                        reader.readAsDataURL(file)
                    }))
                )

                /* 2. формируем объект с дисциплиной */
                const new_discipline = {
                    name: this.title.trim(),
                    documents: docs
                }

                /* 3. Отправляем запрос */
                const response = await axios.post(`/api/users/me/disciplines/add`,
                    new_discipline,
                    { headers: { 'Authorization': `Bearer ${accessToken}` } }
                );

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
        }
    }
})
</script>

<style scoped>
.title {
    font-size: 24px;
}

/* горизонтальная лента документов */
.documents-scroll{
    flex-wrap: nowrap;  /* запрещаем перенос элементов */
    overflow-x: auto;   /* включаем горизонтальный скролл */
    overscroll-behavior-x: contain;
    scroll-snap-type: x mandatory;

    scrollbar-width: thin;

    flex: 0 0 auto; /* Предотвращаем сужение по вертикали */

    padding-bottom: .4rem;
    box-sizing: content-box;
}
.documents-scroll::-webkit-scrollbar-thumb{
    background: #c2c2c2;
    border-radius: 4px;
}

/* карточка файла (желательно задать фиксированную минимальную ширину) */
.file-item {
    width: 130px;
    flex: 0 0 auto;
    /* для выравнивания «Удалить файл» внизу */
    display: flex;
    flex-direction: column;
    align-items: center;
}

/* Подпись под иконкой */
.file-item small{
    /* фиксированная высота = 2 строки по 1.2 em + зазор */
    min-height: calc(1.2em * 2);
    max-height: calc(1.2em * 2);

    text-align: center;
    line-height: 1.2;
    margin-top: .25rem;

    /* обрезка до двух строк */
    display: -webkit-box;
    -webkit-line-clamp: 2;   /* количество строк */
    line-clamp: 2;           /* стандартное свойство для совместимости */
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* Кнопка «удалить» всегда прижимается к низу карточки */
.file-item .delete_file{
    margin-top: auto;
    font-size: 1rem;
    font-size: 0.9rem;
}

.delete_file {
    color: #5B5A5A;
    text-decoration: none;
}

.delete_file:hover {
    text-decoration: underline;
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