<template>
  <div class="page">
    <div class="page-header">
      <div>
        <div class="page-title">Memory Recall</div>
        <div class="page-subtitle">{{ data?.total ?? 0 }} patterns in memory</div>
      </div>
      <button @click="load">Refresh</button>
    </div>
    <div class="filters">
      <select v-model="filters.strategy_id" @change="resetAndLoad">
        <option value="">All strategies</option>
        <option value="btc-momentum-v3">btc-momentum-v3</option>
        <option value="eth-mean-reversion">eth-mean-reversion</option>
        <option value="sol-breakout-alpha">sol-breakout-alpha</option>
        <option value="xrp-sentiment-v2">xrp-sentiment-v2</option>
      </select>
      <select v-model="filters.pattern_type" @change="resetAndLoad">
        <option value="">All pattern types</option>
        <option value="BULLISH_MOMENTUM">Bullish Momentum</option>
        <option value="REVERSAL_SIGNAL">Reversal Signal</option>
        <option value="BREAKOUT">Breakout</option>
        <option value="ACCUMULATION">Accumulation</option>
        <option value="HIGH_VOLATILITY">High Volatility</option>
      </select>
      <input v-model="filters.min_confidence" placeholder="Min confidence (0-1)" type="number" min="0" max="1" step="0.05" style="width:180px" @input="resetAndLoad" />
      <button @click="clearFilters">Clear</button>
    </div>
    <div v-if="loading" class="loading">Loading…</div>
    <div v-else-if="error" class="error-msg">{{ error }}</div>
    <table v-else-if="data">
      <thead>
        <tr>
          <th>Memory ID</th>
          <th>Strategy</th>
          <th>Pattern Type</th>
          <th>Confidence</th>
          <th>Recall Count</th>
          <th>Last Recalled</th>
          <th>Description</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="m in data.items" :key="m.memory_id">
          <td class="mono" style="font-size:11px">{{ m.memory_id }}</td>
          <td class="mono" style="font-size:11px;color:var(--accent)">{{ m.strategy_id }}</td>
          <td><span class="badge info">{{ m.pattern_type }}</span></td>
          <td>
            <div style="display:flex;align-items:center;gap:6px">
              <div class="conf-bar"><div class="conf-fill" :style="{ width: (m.confidence * 100) + '%', background: confColor(m.confidence) }"></div></div>
              {{ (m.confidence * 100).toFixed(0) }}%
            </div>
          </td>
          <td>{{ m.recall_count }}</td>
          <td class="mono" style="font-size:11px">{{ relTime(m.last_recalled_ms) }}</td>
          <td style="font-size:11px;color:var(--text-muted);max-width:300px">{{ m.description }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from "vue"
import { useFetch } from "../composables/useFetch"

interface MemRecord { memory_id: string; strategy_id: string; pattern_hash: string; confidence: number; recall_count: number; last_recalled_ms: number; pattern_type: string; description: string }
interface MemResponse { items: MemRecord[]; total: number; page: number; total_pages: number }

const filters = reactive({ strategy_id: "", pattern_type: "", min_confidence: "", page: 1 })
const { data, loading, error, execute } = useFetch<MemResponse>("")

function buildUrl() {
  const p = new URLSearchParams()
  if (filters.strategy_id) p.set("strategy_id", filters.strategy_id)
  if (filters.pattern_type) p.set("pattern_type", filters.pattern_type)
  if (filters.min_confidence) p.set("min_confidence", filters.min_confidence)
  p.set("page", String(filters.page))
  return `/api/memory-recall?${p}`
}
function load() { execute(buildUrl()) }
function resetAndLoad() { filters.page = 1; load() }
function clearFilters() { filters.strategy_id = ""; filters.pattern_type = ""; filters.min_confidence = ""; resetAndLoad() }

onMounted(load)

function confColor(v: number) { return v >= 0.75 ? "var(--success)" : v >= 0.5 ? "var(--warn)" : "var(--error)" }
function relTime(ms: number) {
  const diff = Date.now() - ms
  if (diff < 60_000) return `${Math.round(diff / 1000)}s ago`
  if (diff < 3_600_000) return `${Math.round(diff / 60_000)}m ago`
  return `${Math.round(diff / 3_600_000)}h ago`
}
</script>

<style scoped>
.mono { font-family: monospace; font-size: 12px; }
.conf-bar { width: 60px; height: 6px; background: var(--bg3); border-radius: 3px; overflow: hidden; }
.conf-fill { height: 100%; border-radius: 3px; transition: width 0.3s; }
</style>
