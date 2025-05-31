<template>
    <div :class="['main_panel pt-4 d-flex flex-column', showPanel ? 'panel_open' : 'panel_closed']">
        <div class="header d-flex align-items-center"
            :style="{ left: showPanel ? '16.666666%' : '0', width: showPanel ? '83.333333%' : '100%' }">
            <button class="btn close_panel p-0" @click="$emit('togglePanel')">
                <img src="@/assets/close_panel.svg" alt="Закрыть панель" width="43" style="cursor: pointer" />
            </button>

            <div class="header_name ms-4">
                {{ pageTitle }}
            </div>
        </div>
        <div class="main_area d-flex flex-column flex-grow-1 chat_content">
            <div class="content_wrapper mx-auto">
                <slot></slot>
            </div>
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
        pageTitle: {
            type: String,
            default: ''
        }
    },
    emits: ['togglePanel'],
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

.header_name {
    font-size: 24px;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
}

.main_panel {
  position: relative;
  height: 100vh;
  overflow: hidden; /* главная панель не скроллится */
  transition: margin-left 0.3s ease, width 0.3s ease;
}
.panel_open   { margin-left: 16.6666%; width: 83.3333%; }
.panel_closed { margin-left: 0;         width: 100%;     }

.main_area {
  position: absolute;
  top: 60px; bottom: 0; left: 0; right: 0;
  overflow-y: auto;
  overflow-x: hidden;
}

/* центр контента и ограничение по ширине */
.content_wrapper {
  max-width: 1250px;
  width: 100%;
  margin: 0 auto;
  padding: 1rem;
  box-sizing: border-box;

  display:flex;
  flex-direction:column;
  min-height:100%;
}
</style>