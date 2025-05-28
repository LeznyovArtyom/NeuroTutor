<template>
    <div class="title mt-5">Название работы</div>
    <input class="form-control mt-3" v-model="work.name" />
    <div class="title mt-5">Задание</div>
    <textarea class="form-control mt-3" rows="20" v-model="work.task"></textarea>
    <div class="d-flex mt-5 gap-4">
        <div class="title text-nowrap">Номер работы</div>
        <select class="form-select w-auto" v-model="work.number">
            <option v-for="number in Array.from({ length: work.number }, (_, i) => i + 1)" :value="number">{{ number }}
            </option>
        </select>
    </div>
    <div class="d-flex justify-content-between mt-5">
        <div class="document_container me-3">
            <div class="title">Документы</div>
            <div class="dropdown mt-3" data-bs-auto-close="outside">
                <button class="btn btn-outline-secondary dropdown-toggle w-100 text-start" data-bs-toggle="dropdown"
                    data-bs-display="static" data-bs-flip="false">
                    {{ docsLabel }}
                </button>

                <div class="dropdown-menu documents_menu p-2" @click.stop ref="docsMenu">
                    <label class="dropdown-item">
                        <input type="checkbox" class="form-check-input me-2" :checked="isNone" @change="toggleNone">
                        Без документов
                    </label>

                    <div class="dropdown-divider my-1"></div>

                    <label v-for="document in documents" :key="document.id" class="dropdown-item">
                        <input type="checkbox" class="form-check-input me-2" :value="document.id"
                            v-model="work.document_ids" :checked="work.document_ids.includes(document.id)"
                            @change="toggleDoc(document.id, $event)">
                        {{ document.name }}
                    </label>
                </div>
            </div>
        </div>
        <div class="section_container">
            <div class="title">Раздел / Тема / Глава</div>
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
import Cookies from 'js-cookie';

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
                document_ids: [] as number[],
                document_section: ''
            },
            documents: [] as Array<{ id: number; name: string }>
        }
    },
    computed: {
        isNone(): boolean {
            return this.work.document_ids.length === 0
        },
        docsLabel(): string {
            if (this.isNone) return 'Без документов'
            return `Выбрано: ${this.work.document_ids.length}`
        },
        canSubmit(): boolean {
            return this.work.name.trim().length > 0 &&
                this.work.task.trim().length > 0 &&
                this.work.number > 0
        }
    },
    methods: {
        toggleNone(e: Event) {
            if ((e.target as HTMLInputElement).checked) {
                this.work.document_ids = []  // очищаем выбор документов
            }
        },
        /* клик по документу */
        toggleDoc(id: number, e: Event) {
            const checked = (e.target as HTMLInputElement).checked
            const arr = this.work.document_ids

            if (checked) {  // добавить
                if (!arr.includes(id)) arr.push(id)
            } else {        // убрать
                const idx = arr.indexOf(id)
                if (idx !== -1) arr.splice(idx, 1)
            }
        },
        // Гладкое колесо при прокрутке документов
        initSmoothWheel() {
            const box = this.$refs.docsMenu as HTMLElement | undefined
            if (!box) return

            const STEP = 32          // высота одной строки (px)
            const MAX_DY = STEP * 3  // сколько максимум забираем за один event

            box.addEventListener('wheel', e => {
                e.preventDefault()

                /* нормализуем колёсико */
                let dy = Math.sign(e.deltaY) * STEP    // 1 клик = 1 строка
                if (Math.abs(e.deltaY) > STEP)         // тач-пад / очень быстро
                    dy = Math.sign(e.deltaY) * MAX_DY  // режем до 3 строк

                box.scrollBy({ top: dy, left: 0, behavior: 'smooth' })
            }, { passive: false })
        },
        async add_work() {
            if (!this.canSubmit) return

            try {
                const accessToken = Cookies.get('access_token');

                const new_work = {
                    name: this.work.name,
                    task: this.work.task,
                    number: this.work.number,
                    document_ids: this.work.document_ids,
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
                const accessToken = Cookies.get('access_token');

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
                    console.error('Произошла ошибка при получении дисциплины:', error);
                }
            }
        }
    },
    mounted() {
        this.get_discipline_info();
        this.initSmoothWheel();
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

.documents_menu {
    min-width: 350px;
    margin-top: 1px;
    max-height: 155px;
    overflow-y: auto;
    /* scroll-behavior: smooth; */
    /* плавная прокрутка */
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

.add_button {
    background-color: #53B1F5;
}
</style>