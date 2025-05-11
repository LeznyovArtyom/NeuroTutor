<template>
    <div class="container-fluid">
        <!-- Левая панель -->
        <LeftPanel :showPanel="showPanel" :getCookie="getCookie" />

        <!-- Основная область -->
        <MainPanel :showPanel="showPanel" :pageTitle="pageTitle" @togglePanel="togglePanel">
            <router-view />
        </MainPanel>
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
    computed: {
        // берём заголовок из meta текущего маршрута
        pageTitle(): string {
            return String(this.$route.meta.title ?? '')
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
