<template>
  <div class="page">
    <div class="page-header">
      <div><div class="page-title">Audit Trail</div><div class="page-subtitle">Security and policy events</div></div>
      <button @click="load">Refresh</button>
    </div>
    <div class="filters">
      <select v-model="filters.severity" @change="resetAndLoad">
        <option value="">All severities</option>
        <option value="WARN">WARN</option>
        <option value="ERROR">ERROR</option>
      </select>
    </div>
    <div v-if="loading" class="loading">Loading…</div>
    <div v-else-if="error" class="error-msg">{{ error }}</div>
    <table v-else-if="data">
      <thead><tr><th>Time</th><th>Severity</th><th>Type</th><th>Message</th></tr></thead>
      <tbody>
        <tr v-for="ev in data.items" :key="ev.id">
          <td class="mono">{{ ts(ev.ts_ms) }}</td>
          <td><span class="badge" :class="ev.severity.toLowerCase()">{{ ev.severity }}</span></td>
          <td class="mono" style="font-size:11px;color:var(--text-muted)">{{ ev.event_type }}</td>
          <td style="color:var(--text-muted)">{{ ev.message }}</td>
        </tr>
      </tbody>
    </table>
    <div class="pagination" v-if="data">
      <span>{{ data.total }} entries</span>
      <button :disabled="filters.page <= 1" @click="prevPage">‹</button>
      <span>{{ data.page }} / {{ data.total_pages }}</span>
      <button :disabled="filters.page >= data.total_pages" @click="nextPage">›</button>
    </div>
  </div>
</template>
<script setup lang="ts">
import { reactive, onMounted } from "vue"
import { useFetch } from "../composables/useFetch"
interface Item { id: string; ts_ms: number; event_type: string; severity: string; message: string }
interface Resp { items: Item[]; total: number; page: number; total_pages: number }
const filters = reactive({ severity: "", page: 1 })
const { data, loading, error, execute } = useFetch<Resp>("")
function buildUrl() {
  const p = new URLSearchParams()
  if (filters.severity) p.set("severity", filters.severity)
  p.set("page", String(filters.page))
  return `/api/audit-trail?${p}`
}
function load() { execute(buildUrl()) }
function resetAndLoad() { filters.page = 1; load() }
function prevPage() { if (filters.page > 1) { filters.page--; load() } }
function nextPage() { if (data.value && filters.page < data.value.total_pages) { filters.page++; load() } }
onMounted(load)
function ts(ms: number) { return new Date(ms).toLocaleString("tr-TR") }
</script>
<style scoped>.mono { font-family: monospace; font-size: 12px; }</style>
