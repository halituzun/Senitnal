<template>
  <nav class="navbar">
    <div class="nav-brand">
      <span class="brand-icon">◈</span>
      <span class="brand-name">Senitnal</span>
    </div>
    <div class="nav-links">
      <router-link to="/dashboard">Dashboard</router-link>
      <div class="nav-section-label">Intelligence</div>
      <router-link to="/evidence">Evidence</router-link>
      <router-link to="/observer-ledger">Ledger</router-link>
      <router-link to="/ingress-preview">Ingress</router-link>
      <router-link to="/sources">Sources</router-link>
      <div class="nav-section-label">Decisions</div>
      <router-link to="/decisions">Decisions</router-link>
      <router-link to="/memory-recall">Memory</router-link>
      <router-link to="/replay">Replay</router-link>
      <router-link to="/portfolio">Portfolio</router-link>
      <div class="nav-section-label">System</div>
      <router-link to="/health">Health</router-link>
      <router-link to="/policy">Policy</router-link>
      <router-link to="/audit-trail">Audit Trail</router-link>
      <div class="nav-section-label">Adapters</div>
      <router-link to="/adapters">Adapters</router-link>
      <router-link to="/adapter-trust">Trust</router-link>
      <router-link to="/source-trust">Trust</router-link>
      <router-link to="/exchanges">Exchanges</router-link>
      <div class="nav-section-label">Config</div>
      <router-link to="/credentials">Credentials</router-link>
      <router-link to="/ideas">Ideas</router-link>
    </div>
    <div class="nav-footer">
      <div class="nav-user">{{ authStore.email ?? "—" }}</div>
      <button class="logout-btn" @click="handleLogout">Sign out</button>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { useAuthStore } from "../stores/auth"
import { useRouter } from "vue-router"

const authStore = useAuthStore()
const router = useRouter()

async function handleLogout() {
  await authStore.logout()
  await router.push("/login")
}
</script>

<style scoped>
.navbar {
  width: 200px;
  min-width: 200px;
  background: var(--bg2);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow-y: auto;
  padding: 0;
}
.nav-brand {
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid var(--border);
}
.brand-icon { font-size: 20px; color: var(--accent); }
.brand-name { font-size: 15px; font-weight: 700; letter-spacing: 0.02em; }
.nav-links { flex: 1; padding: 8px 0; display: flex; flex-direction: column; }
.nav-links a {
  padding: 6px 16px;
  font-size: 13px;
  color: var(--text-muted);
  display: block;
}
.nav-links a:hover { color: var(--text); background: var(--bg3); text-decoration: none; }
.nav-links a.router-link-active { color: var(--accent); background: rgba(88,166,255,0.08); }
.nav-section-label {
  padding: 10px 16px 4px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #4d5566;
}
.nav-footer { padding: 12px 16px; border-top: 1px solid var(--border); }
.nav-user { font-size: 11px; color: var(--text-muted); margin-bottom: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.logout-btn { width: 100%; font-size: 12px; padding: 4px 8px; }
</style>
