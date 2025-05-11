<template>
    <main>
        <div class="container-fluid">
            <div class="row">
                <transition name="slide-fade">
                    <div v-if="showPanel" class="left_panel pt-3 d-flex flex-column"
                        style="position: fixed; top: 0; left: 0; width: 16.666666%; height: 100vh;">
                        <div class="namelogo d-flex align-items-center justify-content-center">
                            <div class="logo"><img src="@/assets/neurotutor_logo.svg" alt="Лого" width="66" /></div>
                            <div class="site_name ms-2 fw-semibold" style="font-size: 36px">NeuroTutor</div>
                        </div>
                        <div class="d-flex align-items-center mt-4 justify-content-center">
                            <button class="btn new_chat_button" @click="add_chat"
                                style="background-color: #d74f37; color: white; width: 247px; height: 42px">
                                <img src="@/assets/new_chat.svg" alt="Новый чат" width="25" class="me-2" />Новый чат
                            </button>
                        </div>
                        <div class="chats_list_name mt-4 mb-2 ms-3 fw-medium">Список чатов</div>
                        <div class="chats_list">
                            <div v-for="chat in chats" :key="chat.id" class="d-flex align-items-center px-3 rounded-2"
                                :class="{ selected_chat: selectedChatId === chat.id }"
                                style="height: 33px; cursor: pointer" @click="selectedChat(chat.id)">
                                <span v-if="editingChatId !== chat.id">
                                    {{ truncateString(chat.title, 25) }}
                                </span>
                                <input v-else v-model="editingTitle"
                                    class="form-control border-0 bg-transparent flex-grow-1 p-0" autofocus
                                    @keydown.enter="saveChatTitle(chat.id)" @keydown.esc="cancelEdit"
                                    @blur="saveChatTitle(chat.id)" style="font-size: inherit;" />
                                <!-- троеточие + маленькое меню -->
                                <div class="position-relative ms-auto">
                                    <button class="btn rounded-5" @click.stop="toggleMenu(chat.id)">
                                        <i class="bi bi-three-dots-vertical"></i>
                                    </button>

                                    <!-- меню с кнопками редактирования и удаления -->
                                    <transition name="fade">
                                        <ul v-if="menuFor === chat.id"
                                            class="chat-menu list-unstyled position-absolute bg-white border rounded-2 shadow-sm p-1 z-3"
                                            style="right: 0; top: 100%; min-width: 160px">
                                            <li class="chat-menu-item px-3 py-2 small" @click="startEdit(chat)">
                                                <i class="bi bi-pencil me-1"></i> Изменить
                                            </li>
                                            <li class="chat-menu-item px-3 py-2 small text-danger"
                                                @click="removeChat(chat.id)">
                                                <i class="bi bi-trash me-1"></i> Удалить
                                            </li>
                                        </ul>
                                    </transition>
                                </div>
                            </div>
                        </div>

                        <div class="d-flex justify-content-center mt-auto mb-4 position-relative">
                            <button
                                class="btn profile_button text-white d-flex align-items-center justify-content-center rounded-3"
                                style="background-color:#8eb3ce; width:247px; height:42px" @click="toggleProfilePopup">
                                Профиль
                            </button>

                            <!-- ПОПАП -->
                            <transition name="fade">
                                <div v-if="showProfilePopup" class="profile-popup p-3" ref="popup">
                                    <div class="fw-semibold mb-2 text-center">Ваш профиль</div>
                                    <div class="small mb-3">Логин: <b>{{ user.login }}</b></div>

                                    <button class="btn btn-sm btn-outline-primary w-100 mb-2" data-bs-toggle="modal"
                                        data-bs-target="#changeUserModal">
                                        Изменить
                                    </button>
                                    <button class="btn btn-sm btn-outline-danger w-100" @click="logout">
                                        Выйти
                                    </button>
                                </div>
                            </transition>
                        </div>
                    </div>
                </transition>
                <div :class="['main-column pt-4 d-flex flex-column', showPanel ? 'col-10 offset-2' : 'col-12']"
                    style="height: calc(100vh - 60px); position: relative;">
                    <div class="header d-flex align-items-center"
                        :style="{ left: showPanel ? '16.666666%' : '0', width: showPanel ? '83.333333%' : '100%' }">
                        <button class="btn close_panel p-0" @click="togglePanel()">
                            <img src="@/assets/close_panel.svg" alt="Закрыть панель" width="43" class="close_panel"
                                style="cursor: pointer" />
                        </button>
                        <select class="mode border-0 rounded-3 no-arrow d-flex align-items-center ms-4"
                            v-model="selectedMode" style="width: 200px; font-size: 20px">
                            <option value="base">Базовый</option>
                            <option value="peft">PEFT</option>
                            <option value="rag">RAG</option>
                            <option value="peft+rag">PEFT+RAG</option>
                        </select>
                    </div>
                    <div class="main_area px-5 d-flex flex-column flex-grow-1 chat_content mx-auto"
                        style="overflow-y: auto; padding-bottom: 62px; width: 1250px;">
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
                        <div class="write_message d-flex align-items-center border-0 p-3 rounded-5" :class="{ 'panel-open': showPanel }">
                            <input type="text" placeholder="Чем могу быть вам полезен?" v-model="inputText"
                                @keydown.enter="sendMessage"
                                class="w-100 border-0 bg-transparent form-control shadow-none" />
                            <button class="btn ms-4 rounded-5" style="background-color: #d9d9d9"
                                :disabled="sending || !inputText.trim()" @click="sendMessage">
                                <img src="@/assets/arrow.svg" alt="Отправить" width="15" />
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <div class="modal fade" id="changeUserModal" tabindex="-1" aria-labelledby="changeUserModalLabel"
        aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content">
                <!-- Форма просмотра и изменения задачи -->
                <form @submit.prevent="submitUpdatedFields()">
                    <div class="modal-header">
                        <h1 class="modal-title fs-5" id="changeUserModalLabel">Изменить данные</h1>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Закрыть"></button>
                    </div>
                    <div class="modal-body">
                        <!-- Логин -->
                        <div class="mb-1">Логин</div>
                        <input type="text" name="change_login" id="change_login"
                            class="w-100 mb-1 p-1 rounded-1 border-1" v-model="newUserInfo.login"
                            :placeholder="user.login" />
                        <div v-if="errors.login" class="error small text-danger">{{ errors.login }}</div>
                        <!-- Пароль -->
                        <div class="mb-1">Пароль</div>
                        <input type="text" name="change_password" id="change_password"
                            class="w-100 mb-1 p-1 rounded-1 border-1" v-model="newUserInfo.password" />
                        <div v-if="errors.password" class="error small text-danger">{{ errors.password }}</div>
                    </div>
                    <!-- Кнопки закрытия модального окна и сохранения задачи -->
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button>
                        <button type="submit" class="btn btn-primary">Сохранить</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import { marked } from 'marked'
import axios from 'axios'

export default defineComponent({
    name: 'ChatPage',
    data() {
        return {
            showPanel: true,
            showProfilePopup: false,
            markdownConverter: marked,
            user: {
                login: '',
                password: ''
            },
            newUserInfo: {
                login: '',
                password: ''
            },
            errors: {
                login: '' as string,
                password: '' as string,
            },
            chats: [] as Array<{ id: number; title: string; mode: number; created_at: Date }>,
            selectedChatId: null as number | null,
            menuFor: null as number | null, // id чата, для которого открыто меню
            editingChatId: null as number | null,// id редактируемого чата
            editingTitle: '', // буфер для ввода нового названия
            messages: [] as Array<{ id: number; context: string; created_at: Date; sender: string }>,
            inputText: '', // содержимое поля ввода сообщения
            sending: false, // блокируем кнопку пока идёт запрос
            selectedMode: 'base', // выбранный режим (по умолчанию базовый)
        }
    },
    methods: {
        // Получить информацию о пользователе
        async getUserInfo() {
            try {
                const accessToken = this.getCookie('access_token');

                const response = await axios.get(`/api/users/me`, {
                    headers: {
                        'Authorization': `Bearer ${accessToken}`
                    }
                });

                this.user.login = response.data.User.login;
            } catch (error) {
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при получении данных пользователя:', error);
                }
            }
        },
        // Валидация данных пользователя
        submitUpdatedFields() {
            const updatedFields: { login?: string; password?: string } = {};

            if (this.newUserInfo.login) {
                const loginPattern = /^[a-zA-Z0-9]{3,}$/;
                if (!loginPattern.test(this.newUserInfo.login)) {
                    this.errors.login = 'Логин должен быть не менее 3 символов и содержать только буквы и цифры';
                } else {
                    this.errors.login = '';
                    updatedFields.login = this.newUserInfo.login;
                }
            }
            if (this.newUserInfo.password) {
                if (this.newUserInfo.password.length < 6) {
                    this.errors.password = 'Длина пароля должна быть не менее 6 символов';
                } else {
                    this.errors.password = '';
                    updatedFields.password = this.newUserInfo.password;
                }
            }

            if (this.errors.login || this.errors.password) {
                return;
            }

            if (Object.keys(updatedFields).length > 0) {
                this.updateUser(updatedFields);
            } else {
                alert('Нет изменений для сохранения.');
            }
        },
        // Обновить данные пользователя
        async updateUser(updatedFields: { login?: string; password?: string }) {
            try {
                const accessToken = this.getCookie('access_token');

                const response = await axios.put(`/api/users/me/update`,
                    updatedFields,
                    { headers: { 'Authorization': `Bearer ${accessToken}` } }
                );
                if (response.data.new_token) {
                    this.setCookie('access_token', response.data.new_token);
                }
                alert('Данные успешно обновлены');
                this.$router.go(0);
            } catch (error) {
                console.log(error);
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при обновлении данных пользователя:', error);
                }
            }
        },
        // Установить куки для name
        setCookie(name: string, value: string, options: { [key: string]: string | boolean | Date } = {}): void {
            options = {
                path: '/',
                ...options
            };

            if (options.expires instanceof Date) {
                options.expires = options.expires.toUTCString();
            }

            let updatedCookie = encodeURIComponent(name) + "=" + encodeURIComponent(value);

            for (let optionKey in options) {
                updatedCookie += "; " + optionKey;
                let optionValue = options[optionKey];
                if (optionValue !== true) {
                    updatedCookie += "=" + optionValue;
                }
            }

            document.cookie = updatedCookie;
        },
        // Получить куки для name
        getCookie(name: string) {
            let matches = document.cookie.match(new RegExp(
                "(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') + "=([^;]*)"
            ));
            return matches ? decodeURIComponent(matches[1]) : undefined;
        },
        // Выйти из аккаунта
        logout() {
            this.deleteCookie('access_token');
            this.$router.push('/');
        },
        // Удалить куки
        deleteCookie(name: string): void {
            document.cookie = name + '=; Max-Age=-99999999; path=/';
        },

        // Получить все чаты пользователя
        async get_chats() {
            try {
                const accessToken = this.getCookie('access_token');

                const response = await axios.get(`/api/users/me/chat_sessions`,
                    { headers: { 'Authorization': `Bearer ${accessToken}` } }
                );

                this.chats = response.data.ChatSessions.reverse();

            } catch (error) {
                console.log(error);
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при обновлении данных пользователя:', error);
                }
            }
        },
        // Обрезка строки в соответствии с количеством символов
        truncateString(str: string, num: number): string {
            return str.length > num ? str.slice(0, num) + "..." : str; // Функция для обрезки строки и добавления троеточия, если длина строки больше num символов
        },
        // Выбор чата
        async selectedChat(chatId: number) {
            if (this.selectedChatId === chatId) return // повторный клик – ничего не делаем
            this.selectedChatId = chatId
            this.messages = []

            await this.get_messages()
        },
        // Добавление нового чата
        async add_chat() {
            try {
                const accessToken = this.getCookie('access_token');

                const response = await axios.post(`/api/users/me/chat_sessions/add`,
                    {},
                    { headers: { 'Authorization': `Bearer ${accessToken}` } }
                );

                this.get_chats()
                this.selectedChatId = response.data.newChatSessionId;

            } catch (error) {
                console.log(error);
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при добавлении чата:', error);
                }
            }
        },
        // Закрытие меню при клике на него
        toggleMenu(id: number) {
            this.menuFor = this.menuFor === id ? null : id
        },
        // Редактирование названия чата
        startEdit(chat: { id: number; title: string }) {
            this.editingChatId = chat.id;
            this.editingTitle = chat.title;
            this.menuFor = null;  // закрываем меню
            this.$nextTick(() => {
                const inputElement = document.querySelector('input[autofocus]') as HTMLInputElement;
                inputElement?.focus();
            });
        },
        // Отмена редактирования названия чата
        cancelEdit() {
            this.editingChatId = null
        },
        // Сохранение нового названия чата
        async saveChatTitle(id: number) {
            const newTitle = this.editingTitle.trim()
            if (!newTitle) return

            try {
                const token = this.getCookie('access_token')
                await axios.put(`/api/users/me/chat_sessions/${id}/update`, { title: newTitle },
                    { headers: { Authorization: `Bearer ${token}` } }
                );

                this.get_chats()
            } catch (error) {
                console.log(error);
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при изменении чата:', error);
                }
            }

            this.editingChatId = null
        },

        // Удаление чата
        async removeChat(chatId: number) {
            if (this.selectedChatId === chatId) this.selectedChatId = null

            try {
                const token = this.getCookie('access_token')
                const response = await axios.delete(`/api/users/me/chat_sessions/${chatId}/delete`,
                    { headers: { Authorization: `Bearer ${token}` } }
                );

                this.get_chats()
            } catch (error) {
                console.log(error);
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при удалении чата:', error);
                }
            }
        },

        /* --- клик вне меню закрывает его --- */
        handleGlobalClick(e: MouseEvent) {
            const menu = (e.target as HTMLElement).closest('.chat-menu')
            const dots = (e.target as HTMLElement).closest('.bi-three-dots-vertical')
            if (!menu && !dots) this.menuFor = null
        },

        /* переключение боковой панели */
        togglePanel() {
            this.showPanel = !this.showPanel
        },

        /* показ / скрытие поп-апа */
        toggleProfilePopup() {
            this.showProfilePopup = !this.showProfilePopup
        },
        /* закрывать поп-ап при клике мимо */
        handleClickOutside(e: MouseEvent) {
            const popup = this.$refs.popup as HTMLElement | undefined
            const button = (e.target as HTMLElement).closest('.profile_button')
            if (!popup || popup.contains(e.target as Node) || button) return
            this.showProfilePopup = false
        },
        // Получение сообщений из чата
        async get_messages() {
            try {
                const accessToken = this.getCookie('access_token')

                const response = await axios.get(`/api/users/me/chat_sessions/${this.selectedChatId}/messages`,
                    { headers: { 'Authorization': `Bearer ${accessToken}` } }
                );

                this.messages = response.data.Messages

            } catch (error) {
                console.log(error);
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при получении сообщений:', error);
                }
            }
        },

        /* Конфертация текста в Markdown */
        convertMarkdown(text: string) {
            return this.markdownConverter.parse(text)
        },
        // Отправка сообщения
        async sendMessage() {
            const text = this.inputText.trim()
            if (!text || !this.selectedChatId) return

            try {
                const accessToken = this.getCookie('access_token');

                await axios.post(`/api/users/me/chat_sessions/${this.selectedChatId}/messages/add`,
                    { context: text, sender: 'user' },
                    { headers: { 'Authorization': `Bearer ${accessToken}` } }
                );

                await this.get_messages();

                // Добавляем временное сообщение "Думаю" от имени нейросети
                this.messages.push({
                    id: Date.now(), // временный ID
                    context: 'Думаю...',
                    created_at: new Date(),
                    sender: 'ai'
                });

                this.inputText = ''
                this.sending = true

                // Отправляем запрос к нейросети
                const response = await this.fetchAnswer(text);

                // Добавляем ответ нейросети
                await axios.post(
                    `/api/users/me/chat_sessions/${this.selectedChatId}/messages/add`,
                    { context: response, sender: 'ai' },
                    { headers: { 'Authorization': `Bearer ${accessToken}` } }
                );

                // Обновляем список сообщений
                await this.get_messages();

            } catch (error) {
                console.log(error);
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при отправке сообщения:', error);
                }
            }
        },
        // Получение ответа от нейросети
        async fetchAnswer(prompt: string): Promise<string> {
            const token = this.getCookie('access_token')
            const { data } = await axios.post(
                '/api/chat/answer',
                { chat_id: this.selectedChatId, text: prompt, mode: this.selectedMode },
                { headers: { Authorization: `Bearer ${token}` } })
            return data.answer
        },
        // Прокрутка до конца чата
        scrollToEnd() {
            const area = this.$el.querySelector('.main_area') as HTMLElement
            area?.scrollTo({ top: area.scrollHeight })
        },
    },
    mounted() {
        this.getUserInfo();
        this.get_chats()
        // Обработчик клика «вне» поп-апа
        document.addEventListener('click', this.handleClickOutside);
        document.addEventListener('click', this.handleGlobalClick)
    },
    beforeUnmount() {
        document.removeEventListener('click', this.handleClickOutside);
        document.removeEventListener('click', this.handleGlobalClick)
    },
})
</script>

<style scoped>
/* Выбор чата */
.selected_chat {
    background-color: #D9D9D9;
}
.chat-menu-item:hover {
    background: #f5f5f5;
    cursor: pointer;
}
.chat-menu-item+.chat-menu-item {
    border-top: 1px solid #eee;
}

/* Всплывающее окно над кнопкой профиля */
.profile-popup {
    position: absolute;
    bottom: 50px;
    left: 50%;
    transform: translateX(-50%);
    width: 247px;
    min-height: 180px;
    background: #fff;
    border: 1px solid #ccc;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, .15);
    z-index: 1000;
}

/* Анимация появления окна с информацией о пользователе */
.fade-enter-active,
.fade-leave-active {
    transition: opacity .15s ease, transform .15s ease;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
    transform: translateY(8px);
}

.left_panel {
    background-color: #efefef;
    height: 100vh;
}

/* Анимация появления и исчезновения левой панели */
.slide-fade-enter-active,
.slide-fade-leave-active {
    transition: all 0.3s ease;
}

.slide-fade-enter-from,
.slide-fade-leave-to {
    transform: translateX(-100%);
    opacity: 0;
}

.slide-fade-enter-to,
.slide-fade-leave-from {
    transform: translateX(0);
    opacity: 1;
}

/* Кнопка отправки сообщения */
.no-arrow {
    appearance: none;
    /* Убирает стрелку в большинстве браузеров */
    -webkit-appearance: none;
    /* Safari/Chrome */
    -moz-appearance: none;
    /* Firefox */
    background: none;
    border: 1px solid #ccc;
    padding: 8px;
}

/* Анимация появления и исчезновения меню */
.header {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 60px;
    background-color: white;
    z-index: 1000;
    display: flex;
    align-items: center;
    padding: 0 1rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    transition: left 0.3s ease;
}

.main-column {
    margin-top: 60px;
}

.left_panel+.main-column {
    transition: margin-left 0.3s ease;
}

/* поле написания сообщения */
.write_message {
    position: fixed;
    bottom: 1rem;
    right: 0;
    width: 1250px;
    margin: 0 auto;
    background-color: #efefef;
    height: 62px;
    z-index: 1000;
}

.write_message.panel-open {
    left: 16.6666%;
}

.write_message:not(.panel-open) {
    left: 0;
}
</style>
