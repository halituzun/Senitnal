<template>
  <div v-if="isLoginPage || isForbiddenPage">
    <router-view />
  </div>
  <div v-else class="layout">
    <NavBar />
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue"
import { useRoute } from "vue-router"
import NavBar from "@/components/NavBar.vue"

const route = useRoute()
const isLoginPage = computed(() => route.name === "login")
const isForbiddenPage = computed(() => route.name === "forbidden")
</script>

<style scoped>
.layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}
.main-content {
  flex: 1;
  overflow-y: auto;
  background: var(--bg);
}
</style>
