<template>
  <div class="page">
    <div class="page-header">
      <div><div class="page-title">Evidence</div><div class="page-subtitle">Signal evidence bundles</div></div>
      <button @click="load">Refresh</button>
    </div>
    <div class="filters">
      <select v-model="filters.strategy_id" @change="load">
        <option value="">All strategies</option>
        <option value="btc-momentum-v3">btc-momentum-v3</option>
        <option value="eth-mean-reversion">eth-mean-reversion</option>
        <option value="sol-breakout-alpha">sol-breakout-alpha</option>
      </select>
    </div>
    <div v-if="loading" class="loading">Loading…</div>
    <div v-else-if="error" class="error-msg">{{ error }}</div>
    <table v-else-if="data">
      <thead><tr><th>Time</th><th>Strategy</th><th>Message</th></tr></thead>
      <tbody>
        <tr v-for="ev in data.items" :key="ev.id">
          <td class="mono">{{ ts(ev.ts_ms) }}</td>
          <td class="mono" style="font-size:11px;color:var(--accent)">{{ ev.strategy_id ?? "—" }}</td>
          <td style="color:var(--text-muted)">{{ ev.message }}</td>
        </tr>
      </tbody>
    </table>
    <div v-if="data && data.items.length === 0" class="empty">No evidence bundles found</div>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from "vue"
import { useFetch } from "@/composables/useFetch.js"
interface Item { id: string; ts_ms: number; strategy_id: string | null; message: string }
interface Resp { items: Item[]; total: number; page: number; total_pages: number }
const filters = reactive({ strategy_id: "" })
const { data, loading, error, execute } = useFetch<Resp>("")
function buildUrl() {
  const p = new URLSearchParams()
  if (filters.strategy_id) p.set("strategy_id", filters.strategy_id)
  return `/api/evidence?${p}`
}
function load() { execute(buildUrl()) }
onMounted(load)
function ts(ms: number) { return new Date(ms).toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit", second: "2-digit" }) }
</script>
<style scoped>.mono { font-family: monospace; font-size: 12px; }</style>
