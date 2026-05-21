<template>
  <div class="page">
    <div class="page-header">
      <div><div class="page-title">Adapter Trust</div><div class="page-subtitle">Trust band distribution</div></div>
      <button @click="load">Refresh</button>
    </div>
    <div v-if="loading" class="loading">Loading…</div>
    <div v-else-if="error" class="error-msg">{{ error }}</div>
    <div v-else-if="data" class="stat-grid" style="margin-bottom:20px">
      <div class="stat-card" v-for="s in data.summary" :key="s.trust_band">
        <div class="stat-label">{{ s.trust_band }}</div>
        <div class="stat-value" :class="trustClass(s.trust_band)">{{ s.count }}</div>
      </div>
    </div>
    <template v-if="data">
      <div v-for="s in data.summary" :key="s.trust_band" class="band-section">
        <div class="band-header"><span class="badge" :class="trustClass(s.trust_band)">{{ s.trust_band }}</span></div>
        <table v-if="s.adapters.length > 0">
          <thead><tr><th>Adapter ID</th><th>Healthy</th></tr></thead>
          <tbody>
            <tr v-for="a in s.adapters" :key="a.adapter_id">
              <td class="mono" style="font-size:11px">{{ a.adapter_id }}</td>
              <td><span class="badge" :class="a.is_healthy ? 'ok' : 'error'">{{ a.is_healthy ? "Yes" : "No" }}</span></td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty" style="padding:12px">No adapters in this band</div>
      </div>
    </template>
  </div>
</template>
<script setup lang="ts">
import { onMounted } from "vue"
import { useFetch } from "@/composables/useFetch.js"
interface BandAdapter { adapter_id: string; name: string; is_healthy: boolean; is_fresh: boolean }
interface BandSummary { trust_band: string; count: number; adapters: BandAdapter[] }
const { data, loading, error, execute: load } = useFetch<{ summary: BandSummary[] }>("/api/adapter-trust")
onMounted(load)
function trustClass(b: string) { return b === "TRUSTED" ? "ok" : b === "PROVISIONAL" ? "warn" : "error" }
</script>
<style scoped>
.band-section { margin-bottom: 20px; }
.band-header { margin-bottom: 8px; }
.mono { font-family: monospace; }
</style>
