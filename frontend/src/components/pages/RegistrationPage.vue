<template>
    <main style="background-color: #EFEFEF;">
        <div class="container-fluid">
            <div class="d-flex flex-column align-items-center justify-content-center vh-100">
                <form class="p-5 rounded-5" style="background-color: #FFFFFF; width: 600px; box-shadow: 0 0 8px #999;"
                    @submit.prevent="registerUser">
                    <div class="header d-flex justify-content-center mb-3" style="font-size: 36px;">Регистрация</div>
                    <div class="line w-100" style="background-color: #EFEFEF; height: 1px"></div>
                    <input type="text" placeholder="Фамилия" class="form-control w-100 rounded-4 mt-5" v-model="formData.last_name"
                        style="height: 48px; font-size: inherit;" />
                    <div v-if="errors.last_name" class="error text-danger mx-3">{{ errors.last_name }}</div>
                    <input type="text" placeholder="Имя" class="form-control w-100 rounded-4 mt-3" v-model="formData.first_name"
                        style="height: 48px; font-size: inherit;" />
                    <div v-if="errors.first_name" class="error text-danger mx-3">{{ errors.first_name }}</div>
                    <select class="form-select w-100 rounded-4 mt-3" v-model="formData.role"
                        style="height: 48px; font-size: inherit;" :class="{'text-muted': !formData.role}">
                        <option value="" disabled selected>Выберите роль</option>
                        <option value="student">Студент</option>
                        <option value="teacher">Преподаватель</option>
                    </select>
                    <div v-if="errors.role" class="error text-danger mx-3">{{ errors.role }}</div>
                    <input type="text" placeholder="Логин" class="form-control w-100 rounded-4 mt-3" v-model="formData.login"
                        style="height: 48px; font-size: inherit;" />
                    <div v-if="errors.login" class="error text-danger mx-3">{{ errors.login }}</div>
                    <input type="password" placeholder="Пароль" class="form-control w-100 rounded-4 mt-3" v-model="formData.password"
                        style=" height: 48px; font-size: inherit;" />
                    <div v-if="errors.password" class="error text-danger mx-3">{{ errors.password }}</div>
                    <div class="d-flex justify-content-center mb-3 mt-4">
                        <button type="submit"
                            class="btn d-flex justify-content-center text-white rounded-3"
                            style="background-color: #53B1F5; width: 295px; height: 48px; font-size: inherit;">Зарегистрироваться</button>
                    </div>
                    <div class="d-flex justify-content-center">
                        <RouterLink to="/authorization">Войти</RouterLink>
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
    name: 'RegistrationPage',
    data() {
        return {
            /**
             * Данные формы регистрации
             *    last_name - фамилия пользователя
             *    first_name - имя пользователя
             *    role - роль пользователя
             *    login - логин пользователя
             *    password - пароль пользователя
             */
            formData: {
                last_name: '' as string,
                first_name: '' as string,
                role: '' as string,
                login: '' as string,
                password: '' as string,
            },
            /**
             * Текст отображения ошибок под полями ввода
             *    last_name - фамилия пользователя
             *    first_name - имя пользователя
             *    role - роль пользователя
             *    login - логин пользователя
             *    password - пароль пользователя
             */
            errors: {
                last_name: '' as string,
                first_name: '' as string,
                role: '' as string,
                login: '' as string,
                password: '' as string,
            }
        }
    },
    methods: {
        // Влидация фамилии
        validateLastName(): boolean {
            // При пустом значении
            if (!this.formData.last_name) {
                this.errors.last_name = 'Заполните поле';
                return false;
            }
            this.errors.last_name = '';
            return true;
        },
        // Валидация имени
        validateFirstName(): boolean {
            // При пустом значении
            if (!this.formData.first_name) {
                this.errors.first_name = 'Заполните поле';
                return false;
            }
            this.errors.first_name = '';
            return true;
        },
        // Валидация роли
        validateRole(): boolean {
            // При пустом значении
            if (!this.formData.role) {
                this.errors.role = 'Выберите роль';
                return false;
            }
            this.errors.role = '';
            return true;
        },
        // Влидация логина
        validateLogin(): boolean {
            const loginPattern = /^[a-zA-Z0-9]{3,}$/;
            // При пустом значении
            if (!this.formData.login) {
                this.errors.login = 'Заполните поле';
                return false;
            }
            // При длине менее 3 символов, наличии не буквы и не цифры
            if (!loginPattern.test(this.formData.login)) {
                this.errors.login = 'Логин должен быть не менее 3 символов и содержать только буквы и цифры';
                return false;
            }
            this.errors.login = '';
            return true;
        },
        // Валидация пароля
        validatePassword(): boolean {
            // При пустом значении
            if (!this.formData.password) {
                this.errors.password = 'Заполните поле';
                return false;
            }
            // При длине менее 6 символов
            if (this.formData.password.length < 6) {
                this.errors.password = 'Длина пароля должна быть не менее 6 символов';
                return false;
            }
            this.errors.password = '';
            return true;
        },
        // Зарегистрировать пользователя
        async registerUser() {
            let success: boolean = true;
            // Валидация всех полей
            if(!this.validateLastName()) success = false;
            if(!this.validateFirstName()) success = false;
            if(!this.validateRole()) success = false;
            if(!this.validateLogin()) success = false;
            if(!this.validatePassword()) success = false;

            if (!success) return;

            const newUser = {
                last_name: this.formData.last_name,
                first_name: this.formData.first_name,
                role: this.formData.role,
                login: this.formData.login,
                password: this.formData.password
            };
            
            try {
                const response = await axios.post(`/api/users/register`, newUser);
                
                if (response.status === 201) {
                    this.formData.last_name = '';
                    this.formData.first_name = '';
                    this.formData.role = '';
                    this.formData.login = '';
                    this.formData.password = '';

                    this.$router.push('/authorization');
                } else {
                    throw new Error(response.data.error || 'Неизвестная ошибка');
                }
            } catch(error: any) {
                if (error.response.status === 409) {
                    alert(error.response.data.detail)
                } else {
                    console.error('Ошибка:', error);
                    alert('Произошла ошибка при регистрации. Попробуйте еще раз.');
                }
            }
        }
    }
})
</script>

<style scoped>
.text-muted{color:#6c757d;}
</style>
