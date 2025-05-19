<template>
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
        <input type="text" placeholder="Напишите вопрос" class="form-control border-0 bg-transparent shadow-none"
            v-model="inputText" @keydown.enter="sendMessage">
        <button class="send_button btn rounded-5 ms-3" :disabled="sending || !inputText.trim()" @click="sendMessage">
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
            chatId: null,
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
                        params: { mode: 'help' }
                    }
                );

                this.chatId = response.data.chat_id;
                this.messages = response.data.messages;
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
        // Отправить сообщение
        async sendMessage() {
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
.write-message {
    background-color: #efefef;
    height: 62px;
}

.send_button {
    background-color: #d9d9d9
}
</style>
