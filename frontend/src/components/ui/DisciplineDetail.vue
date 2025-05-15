<template>
    <div class="d-flex justify-content-between mb-2 mt-5">
        <div class="title">Дисциплина</div>
        <button v-if="!isEditing"
            class="btn action_button change_discipline_name text-white rounded-3 d-flex align-items-center justify-content-center"
            @click="change_discipline_name">Изменить
        </button>
        <div v-else class="d-flex">
            <button
                class="btn action_button cancel_change text-white rounded-3 d-flex align-items-center justify-content-center"
                @click="change_discipline_name">Отмена</button>
            <button
                class="btn action_button save_change text-white rounded-3 ms-3 d-flex align-items-center justify-content-center"
                @click="saveDisciplineName">Сохранить</button>
        </div>
    </div>
    <div v-if="!isEditing" class="mt-3">{{ discipline.name }}</div>
    <input v-else class="form-control mt-3" v-model="newDiscipline.name" />

    <div class="title mb-2 mt-5">Загрузите документы</div>
    <input ref="documentInput" type="file" multiple class="add_documents" @change="upload_new_documents">
    <div class="title mb-2 mt-5">Загруженные документы</div>
    <div class="documents d-flex gap-4 flex-wrap">
        <div v-for="document in documents" :key="document.id" class="d-flex flex-column align-items-center file-item">
            <img src="@/assets/file_icon.svg" alt="Файл" width="100" />
            <small class="text-center mt-1">{{ truncateString(document.name, 22) }}</small>
            <button class="btn btn-link p-0 mt-1" @click="deleteDocument(document)">
                Удалить файл
            </button>
        </div>
    </div>

    <div class="d-flex justify-content-between mt-5">
        <div class="title align-self-end">Работы</div>
        <router-link
            class="btn action_button add_work text-white rounded-3 d-flex align-items-center justify-content-center"
            :to="{ name: 'work-add' }">Добавить
        </router-link>
    </div>

    <table class="table text-nowrap table-hover border-top mt-3">
        <thead class="text-uppercase">
            <tr>
                <th>Название</th>
                <th class="text-center">Действия</th>
            </tr>
        </thead>
        <tbody>
            <tr v-for="work in works">
                <td>
                    <router-link class="work-title text-decoration-none"
                        :to="{ name: 'work-detail', params: { id: id, workId: work.id } }">{{ work.name }}
                    </router-link>
                </td>
                <td class="d-flex gap-3 justify-content-center">
                    <router-link class="btn work_button p-0 m-0 text-center" title="Изменить работу"
                        :to="{ name: 'work-edit', params: { id: id, workId: work.id } }">
                        <i class="bi bi-pencil"></i>
                    </router-link>
                    <button class="btn work_button p-0 m-0 text-center" title="Удалить работу" data-bs-toggle="modal"
                        data-bs-target="#deleteWorkModal" @click="prepareDelete(work)">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        </tbody>
    </table>

    <div class="modal fade" id="deleteWorkModal" tabindex="-1" aria-labelledby="deleteWorkModalLabel"
        aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="deleteWorkModalLabel">Удаление работы</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    Вы действительно хотите удалить работу
                    <strong>{{ workToDelete?.name }}</strong>?
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                        Отмена
                    </button>
                    <button type="button" class="btn btn-danger" @click="delete_work" data-bs-dismiss="modal">
                        Удалить
                    </button>
                </div>
            </div>
        </div>
    </div>
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
            documents: [] as Array<{ id: number; name: string, data: File }>,
            works: [] as Array<{ id: number, name: string, number: number }>,
            workToDelete: { id: 0, name: '' } as { id: number; name: string }
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
                this.documents = response.data.Discipline.documents;
                this.works = response.data.Discipline.works.sort((a: { number: number; }, b: { number: number; }) => a.number - b.number);

            } catch (error) {
                console.log(error);
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при получении дисциплин:', error);
                }
            }
        },
        // Включить режим изменения названия дисциплины
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
                const accessToken = this.getCookie('access_token');
                await axios.put(`/api/users/me/disciplines/${this.id}/update`,
                    { name: newName },
                    { headers: { Authorization: `Bearer ${accessToken}` } }
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
        // Обрезка строки в соответствии с количеством символов
        truncateString(str: string, num: number): string {
            return str.length > num ? str.slice(0, num) + "..." : str;
        },
        // Загрузить новые документы в дисциплину
        async upload_new_documents(e: Event) {
            const input = e.target as HTMLInputElement
            if (!input.files?.length) return

            // конвертируем каждый File → base64
            const docs = await Promise.all(
                Array.from(input.files).map(
                    file =>
                        new Promise<{ name: string; data: string }>((resolve, reject) => {
                            const r = new FileReader()
                            r.onload = () => resolve({ name: file.name, data: (r.result as string).split(',')[1] })
                            r.onerror = reject
                            r.readAsDataURL(file)
                        })
                )
            )
            // Очищаем инпут для загрузки новых документов
            input.value = '';

            try {
                const accessToken = this.getCookie('access_token')
                await axios.put(
                    `/api/users/me/disciplines/${this.id}/update`,
                    { documents: docs },
                    { headers: { Authorization: `Bearer ${accessToken}` } }
                )

                await this.get_discipline_info()
            } catch (error) {
                console.log(error);
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при добавлении новых документов в дисциплину:', error);
                }
            }
        },
        // Удаление документа из дисциплины
        async deleteDocument(document: { id: number; name: string, data: File }) {

            if (!confirm(`Удалить документ "${document.name}"?`)) return

            try {
                const token = this.getCookie('access_token')
                await axios.delete(`/api/disciplines/${this.id}/documents/${document.id}/delete`,
                    { headers: { Authorization: `Bearer ${token}` } }
                );

                this.documents = this.documents.filter(d => d.id !== document.id)
            } catch (error) {
                console.log(error);
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при удалении документа:', error);
                }
            }
        },
        // Подготовка работы для удаления
        prepareDelete(work: { id: number; name: string }) {
            this.workToDelete = work
        },
        // Удалить работу
        async delete_work() {
            try {
                const token = this.getCookie('access_token')
                await axios.delete(`/api/disciplines/${this.id}/work/${this.workToDelete.id}/delete`,
                    { headers: { Authorization: `Bearer ${token}` } }
                );

                this.works = this.works.filter(w => w.id !== this.workToDelete.id);
            } catch (error) {
                console.log(error);
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при удалении работы:', error);
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

.change_discipline_name,
.save_change,
.add_work {
    background-color: #53B1F5;
}

.cancel_change {
    background-color: #F45D5D;
}

.action_button {
    font-size: inherit;
    width: 190px;
    height: 40px;
}

.work_button {
    font-size: inherit;
}

.work-title {
    color: inherit;
}

.work-title:hover {
    color: #0d6efd;
    text-decoration: underline;
}
</style>