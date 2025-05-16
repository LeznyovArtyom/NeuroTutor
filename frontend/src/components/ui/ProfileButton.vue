<template>
    <div class="profile_button_container position-relative">
        <button class="btn profile_button text-white d-flex align-items-center justify-content-center rounded-3"
            @click="toggleProfilePopup">
            Профиль
        </button>

        <!-- ПОПАП Информация о пользователе -->
        <transition name="fade">
            <div v-if="showProfilePopup" class="profile-popup p-3" ref="popup">
                <div class="fw-semibold mb-2 text-center">Ваш профиль</div>
                <div class="small">Фамилия: {{ user.last_name }}</div>
                <div class="small">Имя: {{ user.first_name }}</div>
                <div class="small">Логин: {{ user.login }}</div>
                <div class="small mb-3">Роль: {{ user.role }}</div>

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
    <!-- Модальное окно изменения информации о пользователе -->
    <teleport to="body">
        <ChangeUserInfoModal :user="user" />
    </teleport>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import axios from 'axios';
import Cookies from 'js-cookie';
import { useAuthStore } from '@/stores/auth'
import ChangeUserInfoModal from '@/components/ui/ChangeUserInfoModal.vue';

export default defineComponent({
    name: 'ProfileButton',
    components: {
        ChangeUserInfoModal
    },
    data() {
        return {
            user: {
                last_name: '',
                first_name: '',
                role: '',
                login: ''
            },
            showProfilePopup: false,
        }
    },
    methods: {
        // Получить информацию о пользователе
        async getUserInfo() {
            try {
                const accessToken = Cookies.get('access_token');

                const response = await axios.get(`/api/users/me`,
                    { headers: { 'Authorization': `Bearer ${accessToken}` } }
                );

                this.user.last_name = response.data.User.last_name;
                this.user.first_name = response.data.User.first_name;
                this.user.login = response.data.User.login;
                this.user.role = response.data.User.role;
            } catch (error) {
                if (axios.isAxiosError(error) && error.response?.status === 401) {
                    this.$router.push('/');
                } else {
                    console.error('Произошла ошибка при получении данных пользователя:', error);
                }
            }
        },
        // Выйти из аккаунта
        logout() {
            Cookies.remove('access_token', { path: '/' });
            const auth = useAuthStore();
            auth.clearUser()
            this.$router.push('/');
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
    },
    mounted() {
        this.getUserInfo();
        // Обработчик клика «вне» поп-апа
        document.addEventListener('click', this.handleClickOutside);
    },
    beforeUnmount() {
        document.removeEventListener('click', this.handleClickOutside);
    },
})
</script>

<style scoped>
.profile_button {
    background-color: #8eb3ce;
    width: 247px;
    height: 42px;
    font-size: inherit;
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
</style>