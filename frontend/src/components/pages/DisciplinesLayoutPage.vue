<template>
    <div class="container-fluid">
        <!-- Левая панель -->
        <LeftPanel ref="leftPanel" :showPanel="showPanel" :getCookie="getCookie" />

        <!-- Основная область -->
        <MainPanel :showPanel="showPanel" :pageTitle="pageTitle" @togglePanel="togglePanel">
            <router-view v-slot="{ Component, route }">
                <component :is="Component" v-on="route.name === 'discipline-detail'
                    ? { 'discipline-renamed': onDisciplineRenamed }
                    : {}" />
            </router-view>
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
        onDisciplineRenamed({ id, name }: { id: number; name: string }) {
            (this.$refs.leftPanel as any).updateDisciplineName(id, name)
        },
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
