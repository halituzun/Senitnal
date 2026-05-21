<template>
  <div class="page">
    <div class="page-header">
      <div>
        <div class="page-title">Observer Ledger</div>
        <div class="page-subtitle">{{ data?.total ?? 0 }} events</div>
      </div>
      <button @click="load">Refresh</button>
    </div>

    <div class="filters">
      <select v-model="filters.severity" @change="resetAndLoad">
        <option value="">All severities</option>
        <option value="INFO">INFO</option>
        <option value="WARN">WARN</option>
        <option value="ERROR">ERROR</option>
      </select>
      <input v-model="filters.strategy_id" placeholder="Strategy ID" @input="resetAndLoad" style="width:160px" />
      <input v-model="filters.adapter_id" placeholder="Adapter ID" @input="resetAndLoad" style="width:160px" />
      <input v-model="filters.source" placeholder="Source" @input="resetAndLoad" style="width:140px" />
      <button @click="clearFilters">Clear</button>
    </div>

    <div v-if="loading" class="loading">Loading…</div>
    <div v-else-if="error" class="error-msg">{{ error }}</div>
    <template v-else-if="data">
      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>Severity</th>
            <th>Type</th>
            <th>Source</th>
            <th>Strategy</th>
            <th>Message</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ev in data.items" :key="ev.id">
            <td class="mono">{{ ts(ev.ts_ms) }}</td>
            <td><span class="badge" :class="ev.severity.toLowerCase()">{{ ev.severity }}</span></td>
            <td class="mono" style="font-size:11px;color:var(--text-muted)">{{ ev.event_type }}</td>
            <td class="mono" style="font-size:11px">{{ ev.source }}</td>
            <td class="mono" style="font-size:11px;color:var(--accent)">{{ ev.strategy_id ?? "—" }}</td>
            <td style="max-width:400px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ ev.message }}</td>
          </tr>
        </tbody>
      </table>
      <div class="pagination">
        <span>{{ data.total }} events</span>
        <button :disabled="filters.page <= 1" @click="prevPage">‹ Prev</button>
        <span>{{ data.page }} / {{ data.total_pages }}</span>
        <button :disabled="filters.page >= data.total_pages" @click="nextPage">Next ›</button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from "vue"
import { useFetch } from "@/composables/useFetch.js"

interface LedgerResponse {
  items: Array<{ id: string; ts_ms: number; event_type: string; severity: string; source: string; strategy_id: string | null; adapter_id: string | null; message: string }>
  total: number; page: number; per_page: number; total_pages: number
}

const filters = reactive({ severity: "", strategy_id: "", adapter_id: "", source: "", page: 1 })
const { data, loading, error, execute } = useFetch<LedgerResponse>("")

function buildUrl() {
  const p = new URLSearchParams()
  if (filters.severity) p.set("severity", filters.severity)
  if (filters.strategy_id) p.set("strategy_id", filters.strategy_id)
  if (filters.adapter_id) p.set("adapter_id", filters.adapter_id)
  if (filters.source) p.set("source", filters.source)
  p.set("page", String(filters.page))
  p.set("per_page", "25")
  return `/api/observer-ledger?${p}`
}

function load() { execute(buildUrl()) }
function resetAndLoad() { filters.page = 1; load() }
function prevPage() { if (filters.page > 1) { filters.page--; load() } }
function nextPage() { if (data.value && filters.page < data.value.total_pages) { filters.page++; load() } }
function clearFilters() { filters.severity = ""; filters.strategy_id = ""; filters.adapter_id = ""; filters.source = ""; resetAndLoad() }

onMounted(load)

function ts(ms: number) { return new Date(ms).toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit", second: "2-digit" }) }
</script>

<style scoped>
.mono { font-family: monospace; font-size: 12px; }
</style>
