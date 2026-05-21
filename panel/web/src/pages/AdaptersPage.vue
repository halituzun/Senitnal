<template>
  <div class="page">
    <div class="page-header">
      <div>
        <div class="page-title">Adapters</div>
        <div class="page-subtitle">{{ data?.total ?? 0 }} registered adapters</div>
      </div>
      <div style="display:flex;gap:8px">
        <button @click="load">Refresh</button>
        <router-link to="/adapters/new"><button class="primary">+ Register</button></router-link>
      </div>
    </div>

    <div class="filters">
      <select v-model="filters.trust_band" @change="resetAndLoad">
        <option value="">All trust bands</option>
        <option value="TRUSTED">Trusted</option>
        <option value="PROVISIONAL">Provisional</option>
        <option value="QUARANTINED">Quarantined</option>
        <option value="REVOKED">Revoked</option>
      </select>
      <select v-model="filters.source_family" @change="resetAndLoad">
        <option value="">All families</option>
        <option value="TECHNICAL">Technical</option>
        <option value="NEWS">News</option>
        <option value="SOCIAL">Social</option>
        <option value="ONCHAIN">On-Chain</option>
        <option value="DERIVATIVES">Derivatives</option>
        <option value="MARKET_DATA">Market Data</option>
        <option value="ACCOUNT_DATA">Account Data</option>
        <option value="SENTIMENT">Sentiment</option>
        <option value="RESEARCH">Research</option>
        <option value="INFRASTRUCTURE">Infrastructure</option>
      </select>
      <select v-model="filters.healthy" @change="resetAndLoad">
        <option value="">All health</option>
        <option value="true">Healthy</option>
        <option value="false">Unhealthy</option>
      </select>
      <button @click="clearFilters">Clear</button>
    </div>

    <div v-if="loading" class="loading">Loading…</div>
    <div v-else-if="error" class="error-msg">{{ error }}</div>
    <table v-else-if="data">
      <thead>
        <tr>
          <th>Adapter</th>
          <th>Family</th>
          <th>Trust Band</th>
          <th>Status</th>
          <th>Last Seen</th>
          <th>Error Rate</th>
          <th>Latency</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="a in data.adapters" :key="a.adapter_id">
          <td>
            <div style="font-weight:500">{{ a.name }}</div>
            <div style="font-size:11px;color:var(--text-muted);font-family:monospace">{{ a.adapter_id }}</div>
          </td>
          <td><span class="badge info">{{ a.source_family }}</span></td>
          <td><span class="badge" :class="trustClass(a.trust_band)">{{ a.trust_band }}</span></td>
          <td>
            <span v-if="a.is_healthy" class="badge ok">Healthy</span>
            <span v-else-if="!a.is_fresh && a.is_active" class="badge warn">Stale</span>
            <span v-else-if="!a.is_active" class="badge error">Inactive</span>
            <span v-else class="badge warn">Degraded</span>
          </td>
          <td class="mono">{{ a.last_seen_ms ? relTime(a.last_seen_ms) : "Never" }}</td>
          <td :class="(a.error_rate ?? 0) > 0.1 ? 'error-text' : ''">{{ a.error_rate != null ? (a.error_rate * 100).toFixed(1) + "%" : "—" }}</td>
          <td>{{ a.latency_ms != null ? a.latency_ms + "ms" : "—" }}</td>
        </tr>
      </tbody>
    </table>
    <div v-else class="empty">No adapters found</div>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from "vue"
import { useFetch } from "@/composables/useFetch.js"

interface Adapter { adapter_id: string; name: string; source_family: string; trust_band: string; is_active: boolean; is_fresh: boolean; is_healthy: boolean; last_seen_ms: number | null; latency_ms: number | null; error_rate: number | null; description: string }
interface AdaptersResponse { adapters: Adapter[]; total: number }

const filters = reactive({ trust_band: "", source_family: "", healthy: "" })
const { data, loading, error, execute } = useFetch<AdaptersResponse>("")

function buildUrl() {
  const p = new URLSearchParams()
  if (filters.trust_band) p.set("trust_band", filters.trust_band)
  if (filters.source_family) p.set("source_family", filters.source_family)
  if (filters.healthy) p.set("healthy", filters.healthy)
  return `/api/adapters?${p}`
}

function load() { execute(buildUrl()) }
function resetAndLoad() { load() }
function clearFilters() { filters.trust_band = ""; filters.source_family = ""; filters.healthy = ""; load() }

onMounted(load)

function trustClass(band: string) {
  if (band === "TRUSTED") return "ok"
  if (band === "PROVISIONAL") return "warn"
  if (band === "QUARANTINED") return "error"
  if (band === "REVOKED") return "error"
  return ""
}
function relTime(ms: number) {
  const diff = Date.now() - ms
  if (diff < 60_000) return `${Math.round(diff / 1000)}s ago`
  if (diff < 3_600_000) return `${Math.round(diff / 60_000)}m ago`
  if (diff < 86_400_000) return `${Math.round(diff / 3_600_000)}h ago`
  return `${Math.round(diff / 86_400_000)}d ago`
}
</script>

<style scoped>
.mono { font-family: monospace; font-size: 12px; }
.error-text { color: var(--error); }
</style>
