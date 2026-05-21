<template>
  <div class="page">
    <div class="page-header">
      <div><div class="page-title">Exchanges</div><div class="page-subtitle">Read-only exchange connections — no trade access</div></div>
      <button @click="load">Refresh</button>
    </div>
    <div class="filters">
      <select v-model="filters.status" @change="load">
        <option value="">All status</option>
        <option value="OPERATIONAL">Operational</option>
        <option value="DEGRADED">Degraded</option>
        <option value="DOWN">Down</option>
      </select>
    </div>
    <div v-if="loading" class="loading">Loading…</div>
    <div v-else-if="error" class="error-msg">{{ error }}</div>
    <table v-else-if="data">
      <thead><tr><th>Exchange</th><th>Region</th><th>Status</th><th>Mode</th><th>Last Checked</th><th>Pairs</th><th>Flags</th></tr></thead>
      <tbody>
        <tr v-for="ex in data.exchanges" :key="ex.exchange_id">
          <td><div style="font-weight:500">{{ ex.name }}</div><div class="mono" style="font-size:11px;color:var(--text-muted)">{{ ex.exchange_id }}</div></td>
          <td>{{ ex.region }}</td>
          <td><span class="badge" :class="ex.status === 'OPERATIONAL' ? 'ok' : 'warn'">{{ ex.status }}</span></td>
          <td class="mono" style="font-size:11px">{{ ex.connection_mode }}</td>
          <td class="mono" style="font-size:11px">{{ relTime(ex.last_checked_ms) }}</td>
          <td>{{ ex.pairs_tracked }}</td>
          <td style="font-size:11px;color:var(--text-muted)">no-trade · no-withdraw</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
<script setup lang="ts">
import { reactive, onMounted } from "vue"
import { useFetch } from "../composables/useFetch"
interface Exchange { exchange_id: string; name: string; region: string; status: string; connection_mode: string; trade_enabled: boolean; withdraw_enabled: boolean; last_checked_ms: number; pairs_tracked: number; notes: string }
const filters = reactive({ status: "" })
const { data, loading, error, execute } = useFetch<{ exchanges: Exchange[]; total: number }>("")
function load() {
  const p = new URLSearchParams()
  if (filters.status) p.set("status", filters.status)
  execute(`/api/exchanges?${p}`)
}
onMounted(load)
function relTime(ms: number) {
  const diff = Date.now() - ms
  if (diff < 60_000) return `${Math.round(diff / 1000)}s ago`
  if (diff < 3_600_000) return `${Math.round(diff / 60_000)}m ago`
  return `${Math.round(diff / 3_600_000)}h ago`
}
</script>
<style scoped>.mono { font-family: monospace; font-size: 12px; }</style>
