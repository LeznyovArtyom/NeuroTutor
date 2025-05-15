<template>
    <main style="background-color: #EFEFEF;">
        <div class="container-fluid">
            <div class="d-flex flex-column align-items-center justify-content-center vh-100">
                <div class="p-5 rounded-5" style="background-color: #FFFFFF;">
                    <div class="logo_image d-flex justify-content-center">
                        <img src="@/assets/neurotutor_logo.svg" alt="Лого" width="357">
                    </div>
                    <div class="logo_name d-flex justify-content-center mb-5" style="font-size: 64px;">NeuroTutor</div>
                    <div class="Buttons d-flex justify-content-center mt-5">
                        <button @click="$router.push('/authorization')" class="btn text-white rounded-3 me-4"
                            style="background-color: #53B1F5; width: 295px; height: 48px; font-size: inherit;">Войти</button>
                        <button @click="$router.push('/registration')" class="btn text-white rounded-3"
                            style="background-color: #53B1F5; width: 295px; height: 48px; font-size: inherit;">Зарегистрироваться</button>
                    </div>
                </div>
            </div>
        </div>
    </main>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
    name: 'IndexPage'
})
</script>
