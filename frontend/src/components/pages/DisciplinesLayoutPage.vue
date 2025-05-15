<template>
    <div class="container-fluid">
        <!-- Левая панель -->
        <LeftPanel ref="leftPanel" :showPanel="showPanel" />

        <!-- Основная область -->
        <MainPanel :showPanel="showPanel" :pageTitle="pageTitle" @togglePanel="togglePanel">
            <router-view v-slot="{ Component, route }">
                <component :is="Component" v-on="{
                    ...(route.name === 'discipline-detail' ? { 'discipline-renamed': onDisciplineRenamed } : {}),
                    'set-page-title': setPageTitle
                }" />

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
            pageTitleOverride: '' as string
        }
    },
    computed: {
        // берём заголовок из meta текущего маршрута
        pageTitle(): string {
            return this.pageTitleOverride || String(this.$route.meta.title ?? '')
        }
    },
    watch: {
        // при любом переходе по дочерним роутам сбрасываем override,
        // чтобы вернуться к обычному meta.title
        '$route.name'(newName) {
            this.pageTitleOverride = ''
        }
    },
    methods: {
        onDisciplineRenamed({ id, name }: { id: number; name: string }) {
            (this.$refs.leftPanel as any).updateDisciplineName(id, name)
        },
        setPageTitle(newTitle: string) {
            this.pageTitleOverride = newTitle
        },
        /* переключение боковой панели */
        togglePanel() {
            this.showPanel = !this.showPanel
        },
    }
})
</script>
