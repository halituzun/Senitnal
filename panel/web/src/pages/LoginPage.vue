<template>
  <div class="login-wrap">
    <div class="login-card">
      <div class="login-logo">◈ Senitnal</div>
      <div class="login-subtitle">Intelligence Observation Panel</div>
      <form @submit.prevent="handleLogin">
        <div class="field">
          <label>Email</label>
          <input v-model="email" type="email" placeholder="panel@senitnal.local" autocomplete="email" required />
        </div>
        <div class="field">
          <label>Password</label>
          <input v-model="password" type="password" placeholder="••••••••••••" autocomplete="current-password" required />
        </div>
        <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
        <button type="submit" class="primary" :disabled="loading" style="width:100%;margin-top:8px">
          {{ loading ? "Signing in…" : "Sign in" }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue"
import { useRouter, useRoute } from "vue-router"
import { useAuthStore } from "../stores/auth"

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const email = ref("")
const password = ref("")
const loading = ref(false)
const errorMsg = ref("")

async function handleLogin() {
  loading.value = true
  errorMsg.value = ""
  const result = await auth.login(email.value, password.value)
  loading.value = false
  if (result.ok) {
    const redirect = (route.query["redirect"] as string | undefined) ?? "/dashboard"
    await router.push(redirect)
  } else {
    errorMsg.value = result.error ?? "Login failed"
  }
}
</script>

<style scoped>
.login-wrap {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg);
}
.login-card {
  width: 340px;
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 32px;
}
.login-logo { font-size: 22px; font-weight: 700; color: var(--accent); margin-bottom: 4px; }
.login-subtitle { font-size: 12px; color: var(--text-muted); margin-bottom: 24px; }
.field { margin-bottom: 14px; }
.field label { display: block; font-size: 12px; font-weight: 600; color: var(--text-muted); margin-bottom: 5px; }
.field input { width: 100%; }
</style>
