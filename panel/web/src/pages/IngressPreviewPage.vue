<template>
  <div class="page">
    <div class="page-header">
      <div><div class="page-title">Ingress Preview</div><div class="page-subtitle">Latest intelligence ingress compilation</div></div>
      <button @click="load">Refresh</button>
    </div>
    <div v-if="loading" class="loading">Loading…</div>
    <div v-else-if="error" class="error-msg">{{ error }}</div>
    <template v-else-if="data">
      <div class="stat-grid">
        <div class="stat-card"><div class="stat-label">Total Adapters</div><div class="stat-value">{{ data.adapter_summary.total }}</div></div>
        <div class="stat-card"><div class="stat-label">Active</div><div class="stat-value ok">{{ data.adapter_summary.active }}</div></div>
        <div class="stat-card"><div class="stat-label">Healthy</div><div class="stat-value ok">{{ data.adapter_summary.healthy }}</div></div>
        <div class="stat-card"><div class="stat-label">Stale</div><div class="stat-value" :class="data.adapter_summary.stale > 0 ? 'warn' : 'ok'">{{ data.adapter_summary.stale }}</div></div>
      </div>
      <div class="section-header">Latest Compilation</div>
      <div v-if="data.latest_compilation" class="card">
        <div class="mono" style="font-size:11px;color:var(--text-muted)">{{ ts(data.latest_compilation.ts_ms) }}</div>
        <div style="margin-top:6px">{{ data.latest_compilation.message }}</div>
      </div>
      <div class="section-header">Recent Compilations</div>
      <table>
        <thead><tr><th>Time</th><th>Message</th></tr></thead>
        <tbody>
          <tr v-for="c in data.recent_compilations" :key="c.id">
            <td class="mono" style="font-size:11px">{{ ts(c.ts_ms) }}</td>
            <td style="color:var(--text-muted)">{{ c.message }}</td>
          </tr>
        </tbody>
      </table>
    </template>
  </div>
</template>
<script setup lang="ts">
import { onMounted } from "vue"
import { useFetch } from "../composables/useFetch"
interface Compilation { id: string; ts_ms: number; message: string }
interface IngressResp { latest_compilation: Compilation | null; recent_compilations: Compilation[]; adapter_summary: { total: number; active: number; healthy: number; stale: number } }
const { data, loading, error, execute: load } = useFetch<IngressResp>("/api/ingress-preview")
onMounted(load)
function ts(ms: number) { return new Date(ms).toLocaleString("tr-TR") }
</script>
<style scoped>
.mono { font-family: monospace; }
.section-header { font-size:13px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:.05em;margin:20px 0 10px; }
</style>
