<template>
    <main style="background-color: #EFEFEF;">
        <div class="container-fluid">
            <div class="d-flex flex-column align-items-center justify-content-center vh-100">
                <form class="p-5 rounded-5" style="background-color: #FFFFFF; width: 600px; box-shadow: 0 0 8px #999;"
                    @submit.prevent="authorizeUser">
                    <div class="header d-flex justify-content-center mb-3" style="font-size: 36px;">Авторизация</div>
                    <div class="line w-100" style="background-color: #EFEFEF; height: 1px"></div>
                    <input type="text" placeholder="Логин" class="form-control w-100 rounded-4" v-model="formData.login"
                        style="height: 48px; font-size: inherit; margin-top: 80px;" />
                    <div v-if="errors.login" class="error text-danger mx-2">{{ errors.login }}</div>
                    <input type="password" placeholder="Пароль" class="form-control w-100 rounded-4 mt-4"
                        v-model="formData.password" style=" height: 48px; font-size: inherit;" />
                    <div v-if="errors.password" class="error text-danger mx-2">{{ errors.password }}</div>
                    <div class="d-flex justify-content-center mb-3" style="margin-top: 80px;">
                        <button type="submit" class="btn d-flex justify-content-center text-white rounded-3"
                            style="background-color: #53B1F5; width: 295px; height: 48px; font-size: inherit;">Войти</button>
                    </div>
                    <div class="d-flex justify-content-center">
                        <RouterLink to="/registration">Регистрация</RouterLink>
                    </div>
                </form>
            </div>
        </div>
    </main>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import axios from 'axios';

export default defineComponent({
    name: 'AuthorizationPage',
    data() {
        return {
            /**
             * Данные формы авторизации
             *    login - логин пользователя
             *    password - пароль пользователя
             */
            formData: {
                login: '' as string,
                password: '' as string,
            },
            /**
             * Текст отображения ошибок под полями ввода
             *    login - логин пользователя
             *    password - пароль пользователя
             */
            errors: {
                login: '' as string,
                password: '' as string,
            }
        }
    },
    methods: {
        // Влидация логина
        validateLogin(): boolean {
            // При пустом значении имени
            if (!this.formData.login) {
                this.errors.login = 'Заполните поле';
                return false;
            }
            this.errors.login = '';
            return true;
        },
        // Влидация пароля
        validatePassword(): boolean {
            // При пустом значении имени
            if (!this.formData.password) {
                this.errors.password = 'Заполните поле';
                return false;
            }
            this.errors.password = '';
            return true;
        },
        // Авторизовать пользователя
        async authorizeUser() {
            let success: boolean = true;
            if (!this.validateLogin()) success = false;
            if (!this.validatePassword()) success = false;

            if (!success) return;

            const loginUser = {
                login: this.formData.login,
                password: this.formData.password
            };

            try {
                const response = await axios.post(`/api/users/login`, loginUser);

                if (response.status === 200) {
                    this.formData.login = '';
                    this.formData.password = ''

                    this.setCookie('access_token', response.data.access_token);
                    this.$router.push('/disciplines');
                } else {
                    throw new Error(response.data.error || 'Неизвестная ошибка');
                }
            } catch (error: any) {
                if (error.response.status === 401) {
                    alert(error.response.data.detail)
                } else {
                    console.error('Ошибка:', error);
                    alert('Произошла ошибка при регистрации. Попробуйте еще раз.');
                }
            }
        },
        // Установаить куки для name
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
        }
    }
})
</script>
