<template>
  <div class="page">
    <div class="page-header">
      <div>
        <div class="page-title">Decisions</div>
        <div class="page-subtitle">Decision gate log — {{ data?.total ?? 0 }} records</div>
      </div>
      <button @click="load">Refresh</button>
    </div>

    <div class="filters">
      <select v-model="filters.outcome" @change="resetAndLoad">
        <option value="">All outcomes</option>
        <option value="APPROVED">Approved</option>
        <option value="REJECTED">Rejected</option>
        <option value="ROLLBACK_REQUIRED">Rollback Required</option>
      </select>
      <input v-model="filters.strategy_id" placeholder="Strategy ID" @input="resetAndLoad" style="width:160px" />
    </div>

    <div v-if="loading" class="loading">Loading…</div>
    <div v-else-if="error" class="error-msg">{{ error }}</div>
    <table v-else-if="data">
      <thead>
        <tr>
          <th>Time</th>
          <th>Strategy</th>
          <th>Gate</th>
          <th>Outcome</th>
          <th>Reason</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="d in data.items" :key="d.decision_id">
          <td class="mono">{{ ts(d.ts_ms) }}</td>
          <td class="mono" style="font-size:11px;color:var(--accent)">{{ d.strategy_id }}</td>
          <td class="mono" style="font-size:11px">{{ d.gate_name }}</td>
          <td><span class="badge" :class="outcomeClass(d.outcome)">{{ d.outcome }}</span></td>
          <td style="font-size:11px;color:var(--text-muted);max-width:300px">{{ d.reason }}</td>
        </tr>
      </tbody>
    </table>
    <div class="pagination" v-if="data">
      <span>{{ data.total }} decisions</span>
      <button :disabled="filters.page <= 1" @click="prevPage">‹ Prev</button>
      <span>{{ data.page }} / {{ data.total_pages }}</span>
      <button :disabled="filters.page >= data.total_pages" @click="nextPage">Next ›</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from "vue"
import { useFetch } from "../composables/useFetch"

interface Decision { decision_id: string; ts_ms: number; strategy_id: string; outcome: string; gate_name: string; reason: string }
interface DecisionsResponse { items: Decision[]; total: number; page: number; total_pages: number }

const filters = reactive({ outcome: "", strategy_id: "", page: 1 })
const { data, loading, error, execute } = useFetch<DecisionsResponse>("")

function buildUrl() {
  const p = new URLSearchParams()
  if (filters.outcome) p.set("outcome", filters.outcome)
  if (filters.strategy_id) p.set("strategy_id", filters.strategy_id)
  p.set("page", String(filters.page))
  return `/api/decisions?${p}`
}
function load() { execute(buildUrl()) }
function resetAndLoad() { filters.page = 1; load() }
function prevPage() { if (filters.page > 1) { filters.page--; load() } }
function nextPage() { if (data.value && filters.page < data.value.total_pages) { filters.page++; load() } }

onMounted(load)

function outcomeClass(o: string) {
  if (o === "APPROVED") return "ok"
  if (o === "REJECTED") return "warn"
  return "error"
}
function ts(ms: number) { return new Date(ms).toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit" }) }
</script>
<style scoped>
.mono { font-family: monospace; font-size: 12px; }
</style>
