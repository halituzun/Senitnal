<template>
  <div class="page">
    <div class="page-header">
      <div><div class="page-title">Replay</div><div class="page-subtitle">Strategy simulation history</div></div>
      <button @click="load">Refresh</button>
    </div>
    <div class="filters">
      <select v-model="filters.strategy_id" @change="load">
        <option value="">All strategies</option>
        <option value="bnb-arb-v1">bnb-arb-v1</option>
        <option value="btc-momentum-v3">btc-momentum-v3</option>
      </select>
    </div>
    <div v-if="loading" class="loading">Loading…</div>
    <div v-else-if="error" class="error-msg">{{ error }}</div>
    <table v-else-if="data">
      <thead><tr><th>Time</th><th>Type</th><th>Strategy</th><th>Message</th></tr></thead>
      <tbody>
        <tr v-for="ev in data.replays" :key="ev.id">
          <td class="mono">{{ ts(ev.ts_ms) }}</td>
          <td><span class="badge" :class="ev.event_type === 'REPLAY_COMPLETED' ? 'ok' : 'info'">{{ ev.event_type }}</span></td>
          <td class="mono" style="font-size:11px;color:var(--accent)">{{ ev.strategy_id ?? "—" }}</td>
          <td style="color:var(--text-muted)">{{ ev.message }}</td>
        </tr>
      </tbody>
    </table>
    <div v-if="data && data.replays.length === 0" class="empty">No replay records found</div>
  </div>
</template>
<script setup lang="ts">
import { reactive, onMounted } from "vue"
import { useFetch } from "../composables/useFetch"
interface Item { id: string; ts_ms: number; event_type: string; strategy_id: string | null; message: string }
interface Resp { replays: Item[]; total: number }
const filters = reactive({ strategy_id: "" })
const { data, loading, error, execute } = useFetch<Resp>("")
function load() {
  const p = new URLSearchParams()
  if (filters.strategy_id) p.set("strategy_id", filters.strategy_id)
  execute(`/api/replay?${p}`)
}
onMounted(load)
function ts(ms: number) { return new Date(ms).toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit" }) }
</script>
<style scoped>.mono { font-family: monospace; font-size: 12px; }</style>
