<template>
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
                        <!-- Фамилия -->
                        <div class="mb-1">Фамилия</div>
                        <input type="text" name="change_last_name" id="change_last_name"
                            class="w-100 mb-1 px-2 py-1 rounded-1 border-1" v-model="newUserInfo.last_name"
                            :placeholder="user.last_name" />
                        <div v-if="errors.last_name" class="error small text-danger">{{ errors.last_name }}</div>
                        <!-- Имя -->
                        <div class="mb-1">Имя</div>
                        <input type="text" name="change_first_name" id="change_first_name"
                            class="w-100 mb-1 px-2 py-1 rounded-1 border-1" v-model="newUserInfo.first_name"
                            :placeholder="user.first_name" />
                        <div v-if="errors.first_name" class="error small text-danger">{{ errors.first_name }}</div>
                        <!-- Логин -->
                        <div class="mb-1">Логин</div>
                        <input type="text" name="change_login" id="change_login"
                            class="w-100 mb-1 px-2 py-1 rounded-1 border-1" v-model="newUserInfo.login"
                            :placeholder="user.login" />
                        <div v-if="errors.login" class="error small text-danger">{{ errors.login }}</div>
                        <!-- Пароль -->
                        <div class="mb-1">Пароль</div>
                        <input type="text" name="change_password" id="change_password"
                            class="w-100 mb-1 px-2 py-1 rounded-1 border-1" v-model="newUserInfo.password" />
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
import axios from 'axios'
import Cookies from 'js-cookie';

export default defineComponent({
    name: 'ChangeUserInfoModal',
    props: {
        user: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            newUserInfo: {
                last_name: '',
                first_name: '',
                login: '',
                password: ''
            },
            errors: {
                last_name: '',
                first_name: '',
                login: '',
                password: ''
            }
        }
    },
    methods: {
        // Валидация данных пользователя
        submitUpdatedFields() {
            const updatedFields: { last_name?: string, first_name?: string, login?: string; password?: string } = {};

            if (this.newUserInfo.last_name) {
                updatedFields.last_name = this.newUserInfo.last_name;
            }
            if (this.newUserInfo.first_name) {
                updatedFields.first_name = this.newUserInfo.first_name;
            }
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
        async updateUser(updatedFields: { last_name?: string; first_name?: string; login?: string; password?: string }) {
            try {
                const accessToken = Cookies.get('access_token');

                const response = await axios.put(`/api/users/me/update`,
                    updatedFields,
                    { headers: { 'Authorization': `Bearer ${accessToken}` } }
                );
                if (response.data.new_token) {
                    Cookies.set('access_token', response.data.new_token, { path: '/' });
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
        }
    }
})
</script>