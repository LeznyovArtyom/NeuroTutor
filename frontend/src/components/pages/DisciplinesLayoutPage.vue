<template>
    <div class="container-fluid">
        <!-- Левая панель -->
        <LeftPanel :showPanel="showPanel" :getCookie="getCookie" />

        <!-- Основная область -->
        <MainPanel :showPanel="showPanel" @togglePanel="togglePanel" />
    </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import LeftPanel from '@/components/ui/LeftPanel.vue';
import MainPanel from '@/components/ui/MainPanel.vue';

export default defineComponent({
    name: 'DisciplinesPage',
    components: {
        LeftPanel,
        MainPanel
    },
    data() {
        return {
            showPanel: true,
        }
    },
    methods: {
        // Получить куки для name
        getCookie(name: string) {
            let matches = document.cookie.match(new RegExp(
                "(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') + "=([^;]*)"
            ));
            return matches ? decodeURIComponent(matches[1]) : undefined;
        },
        /* переключение боковой панели */
        togglePanel() {
            this.showPanel = !this.showPanel
        },
    }
})
</script>

<style>
</style>
