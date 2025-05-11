<template>
    <div :class="['main_panel pt-4 d-flex flex-column', showPanel ? 'col-10 offset-2' : 'col-12']"
        style="height: calc(100vh - 60px); position: relative;">
        <div class="header d-flex align-items-center"
            :style="{ left: showPanel ? '16.666666%' : '0', width: showPanel ? '83.333333%' : '100%' }">
            <button class="btn close_panel p-0" @click="$emit('togglePanel')">
                <img src="@/assets/close_panel.svg" alt="Закрыть панель" width="43" style="cursor: pointer" />
            </button>
        </div>
        <div class="main_area px-5 d-flex flex-column flex-grow-1 chat_content mx-auto"
            style="overflow-y: auto; padding-bottom: 62px; width: 1250px;">

        </div>
    </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
    name: 'MainPanel',
    props: {
        showPanel: {
            type: Boolean,
            default: false
        },
    },
    emit: ['togglePanel'],
    methods: {
        truncateString(str: string, maxLength: number) {
            if (str.length > maxLength) {
                return str.slice(0, maxLength) + '...'
            }
            return str
        }
    },
})

</script>

<style scoped>
/* Анимация появления и исчезновения меню */
.header {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 60px;
    background-color: white;
    z-index: 1000;
    padding: 0 1rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    transition: left 0.3s ease;
}

.main_panel {
    margin-top: 60px;
    transition: margin-left 0.3s ease;
}
</style>