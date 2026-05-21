<template>
  <div class="page">
    <div class="page-header">
      <div><div class="page-title">Source Trust</div><div class="page-subtitle">Trust summary by source family</div></div>
      <button @click="load">Refresh</button>
    </div>
    <div v-if="loading" class="loading">Loading…</div>
    <div v-else-if="error" class="error-msg">{{ error }}</div>
    <template v-else-if="data">
      <div v-for="family in data.summary" :key="family.source_family" class="family-card">
        <div class="family-header">
          <span class="badge info">{{ family.source_family }}</span>
          <span style="font-size:12px;color:var(--text-muted)">{{ family.total }} adapters · {{ family.healthy }} healthy · {{ (family.avg_error_rate * 100).toFixed(1) }}% avg error</span>
        </div>
        <table>
          <thead><tr><th>Adapter ID</th><th>Trust Band</th><th>Healthy</th><th>Error Rate</th></tr></thead>
          <tbody>
            <tr v-for="a in family.adapters" :key="a.adapter_id">
              <td class="mono" style="font-size:11px">{{ a.adapter_id }}</td>
              <td><span class="badge" :class="trustClass(a.trust_band)">{{ a.trust_band }}</span></td>
              <td><span class="badge" :class="a.is_healthy ? 'ok' : 'error'">{{ a.is_healthy ? "Yes" : "No" }}</span></td>
              <td :class="(a.error_rate * 100) > 5 ? 'warn-text' : ''">{{ (a.error_rate * 100).toFixed(1) }}%</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>
<script setup lang="ts">
import { onMounted } from "vue"
import { useFetch } from "../composables/useFetch"
interface FamilyAdapter { adapter_id: string; trust_band: string; is_healthy: boolean; error_rate: number }
interface FamilySummary { source_family: string; total: number; healthy: number; avg_error_rate: number; adapters: FamilyAdapter[] }
const { data, loading, error, execute: load } = useFetch<{ summary: FamilySummary[] }>("/api/source-trust")
onMounted(load)
function trustClass(b: string) { return b === "TRUSTED" ? "ok" : b === "PROVISIONAL" ? "warn" : "error" }
</script>
<style scoped>
.family-card { margin-bottom: 24px; }
.family-header { display:flex;align-items:center;gap:12px;margin-bottom:8px; }
.mono { font-family: monospace; }
.warn-text { color: var(--warn); }
</style>
