<template>
    <!-- Загрузка документа для начала работы -->
    <div class="loading_document" v-if="chatStage === 'new'">
        <div class="my-3">Загрузите работу:</div>
        <input type="file" class="form-control" ref="fileInput">
        <button class="btn start_button text-white rounded-3 my-3 d-flex justify-content-center align-items-center"
            :disabled="sending" @click="start_accepting_work">
            Начать сдачу работы
        </button>
    </div>
    <!-- Загрузка исправленного документа -->
    <div class="loading_correct_document" v-if="chatStage === 'returned_for_revision'">
        <div class="my-3">Загрузите исправленную работу:</div>
        <input type="file" class="form-control" ref="fileInputCorrectWork">
        <button class="btn continue_button text-white rounded-3 my-3 d-flex justify-content-center align-items-center"
            :disabled="sending" @click="continue_accepting_work">
            Продолжить сдачу работы
        </button>
    </div>
    <div class="uploaded_document d-flex gap-3 my-3 rounded-2 p-2 w-auto align-self-start" v-if="chatStage !== 'new'">
        <div>Загруженная работа:</div>
        <div class="d-flex gap-1">
            <i class="bi bi-file-earmark-text-fill"></i>
            <div>{{ document_name }}</div>
        </div>
    </div>
    <div ref="scrollContainer" class="messages_container flex-grow-1 overflow-auto mb-3">
        <div v-for="message in messages" class="mb-2 w-100 d-flex"
            :class="{ 'justify-content-end': message.sender === 'user', 'justify-content-start': message.sender === 'ai' }">
            <div v-if="message.sender === 'user'" class="user_message rounded-4 py-2 px-3"
                style="background-color: #efefef; max-width: 70%;">
                <div class="user_name mb-2" style="color: #6c6c6c; text-align: left;">You</div>
                <div class="user_text" style="text-align: right;">{{ message.context }}</div>
            </div>
            <div v-else class="ai_message py-2 px-3" style=" max-width: 100%;">
                <div class="ai_name mb-2" style="color: #6c6c6c;">NeuroTutor</div>
                <div class="ai_text" v-html="convertMarkdown(message.context)"></div>
            </div>
        </div>
    </div>
    <div class="write-message d-flex align-items-center p-3 rounded-5 mt-auto">
        <input type="text" :placeholder="chatStage === 'new' ? 'Сначала загрузите файл' : 'Напишите ответ'"
            class="form-control border-0 bg-transparent shadow-none" v-model="inputText" @keydown.enter="sendMessage">
        <button class="send_button btn rounded-5 ms-3" :disabled="sending || !inputText.trim() || chatStage === 'new'"
            @click="sendMessage">
            <img src="@/assets/arrow.svg" alt="Отправить" width="15" />
        </button>
    </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import { marked } from 'marked'
import axios from 'axios'
import Cookies from 'js-cookie';

export default defineComponent({
    name: "Chat",
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
    emits: ['set-page-title'], // Добавлено как заглушка реальной проблемы
    data() {
        return {
            markdownConverter: marked,
            chatId: null as number | null,
            chatStage: 'new',
            document_name: '',
            messages: [] as Array<{ id: number; context: string; created_at: Date; sender: string }>,
            inputText: '', // содержимое поля ввода сообщения
            sending: false, // блокируем кнопку пока идёт запрос
        }
    },
    methods: {
        // Получить или создать чат
        async fetchOrCreateChat() {
            try {
                const access_token = Cookies.get('access_token');

                const response = await axios.get(`/api/work/${this.workId}/chat`,
                    {
                        headers: { Authorization: `Bearer ${access_token}` },
                        params: { mode: 'acceptance of work' }
                    }
                );

                this.chatId = response.data.chat_id;
                this.messages = response.data.messages;
                this.chatStage = response.data.stage;
                this.document_name = response.data.document_name;
                await this.$nextTick();
                this.scrollToEnd();

            } catch (error) {
                console.log(error);
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при получении или создании чата:', error);
                }
            }
        },
        // Начать приём работы
        async start_accepting_work() {
            if (!this.chatId) return;

            const fileInput = this.$refs.fileInput as HTMLInputElement | undefined;
            if (!fileInput?.files?.length) {
                alert('Пожалуйста, загрузите файл с работой, чтобы я мог приступить к проверке.');
                return;
            }

            const formData = new FormData();
            formData.append('file', fileInput.files[0]);

            this.sending = true;
            try {
                const access_token = Cookies.get('access_token');

                const response = await axios.post(`/api/chat/${this.chatId}/upload`,
                    formData,
                    { headers: { Authorization: `Bearer ${access_token}`, 'Content-Type': 'multipart/form-data' } }
                );

                // ассистент прислал первоое сообщение
                this.messages.push(response.data.ai_message);
                this.chatStage = response.data.chat.stage; // разблокируем поле ввода сообщения
                this.document_name = response.data.chat.document_name;
                await this.$nextTick();
                this.scrollToEnd();
            } catch (err) {
                console.error(err);
                alert('Не удалось отправить файл. Попробуйте ещё раз.');
            } finally {
                this.sending = false;
            }
        },
        // Продолжить приём работы после загрузки исправленной работы
        async continue_accepting_work() {
            if (!this.chatId) return;

            const fileInput = this.$refs.fileInputCorrectWork as HTMLInputElement | undefined;
            if (!fileInput?.files?.length) {
                alert('Вашу работу вернули на доработку. Пожалуйста, загрузите исправленную версию.');
                return;
            }

            const formData = new FormData();
            formData.append('file', fileInput.files[0]);

            this.sending = true;
            try {
                const access_token = Cookies.get('access_token');

                const response = await axios.post(`/api/chat/${this.chatId}/upload`,
                    formData,
                    { headers: { Authorization: `Bearer ${access_token}`, 'Content-Type': 'multipart/form-data' } }
                );

                // ассистент прислал первоое сообщение
                this.messages.push(response.data.ai_message);
                this.chatStage = response.data.chat.stage; // разблокируем поле ввода сообщения
                this.document_name = response.data.chat.document_name;
                await this.$nextTick();
                this.scrollToEnd();
            } catch (err) {
                console.error(err);
                alert('Не удалось отправить файл. Попробуйте ещё раз.');
            } finally {
                this.sending = false;
            }

        },
        // Отправить сообщение
        async sendMessage() {
            if (this.chatStage === 'new') {
                alert('Сначала прикрепите файл работы');
                return;
            }

            const text = this.inputText.trim()
            if (!text || !this.chatId || this.sending) return
            this.inputText = '';
            this.sending = true;

            // мгновенно показываем своё сообщение
            const userIndex = this.messages.push({
                id: Date.now(),
                sender: 'user',
                context: text,
                created_at: new Date()
            }) - 1;

            // временная заглушка «Думаю…»
            const aiIndex = this.messages.push({
                id: Date.now() + 1,
                sender: 'ai',
                context: 'Думаю…',
                created_at: new Date()
            }) - 1;
            await this.$nextTick();
            this.scrollToEnd();

            const access_token = Cookies.get('access_token');

            const response = await axios.post(`/api/chat/${this.chatId}/messages/add`,
                { text: text },
                { headers: { Authorization: `Bearer ${access_token}` } }
            );

            this.messages[userIndex] = response.data.user_message;
            this.messages[aiIndex] = response.data.ai_message;
            await this.$nextTick();
            this.scrollToEnd();

            this.sending = false;
        },
        /* Конвертация текста в Markdown */
        convertMarkdown(text: string) {
            return this.markdownConverter.parse(text)
        },
        // Прокрутка до конца чата
        scrollToEnd() {
            const cont = this.$refs.scrollContainer as HTMLElement | undefined;
            if (cont) cont.scrollTop = cont.scrollHeight;
        }
    },
    async mounted() {
        await this.fetchOrCreateChat();
    }
})
</script>

<style scoped>
.start_button {
    font-size: inherit;
    width: 260px;
    height: 45px;
    background-color: #53B1F5;
}

.continue_button {
    font-size: inherit;
    width: 300px;
    height: 45px;
    background-color: #53B1F5;
}

.uploaded_document {
    background-color: #ececec;
}

.write-message {
    background-color: #efefef;
    height: 62px;
}

.send_button {
    background-color: #d9d9d9
}
</style>
