<template>
  <div class="page">
    <div class="page-header">
      <div><div class="page-title">Policy</div><div class="page-subtitle">Active risk and execution rules</div></div>
      <button @click="load">Refresh</button>
    </div>
    <div v-if="loading" class="loading">Loading…</div>
    <div v-else-if="error" class="error-msg">{{ error }}</div>
    <template v-else-if="data">
      <div class="stat-grid" style="margin-bottom:20px">
        <div class="stat-card">
          <div class="stat-label">Kill Switch</div>
          <div class="stat-value" :class="data.kill_switch_active ? 'error' : 'ok'">{{ data.kill_switch_active ? "ACTIVE" : "Off" }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Active Rules</div>
          <div class="stat-value ok">{{ data.rules.filter((r: Rule) => r.active).length }}</div>
        </div>
      </div>
      <table>
        <thead><tr><th>Rule</th><th>Status</th><th>Threshold</th><th>Current</th><th>Description</th></tr></thead>
        <tbody>
          <tr v-for="r in data.rules" :key="r.rule_id">
            <td><div style="font-weight:500">{{ r.name }}</div><div class="mono" style="font-size:11px;color:var(--text-muted)">{{ r.rule_id }}</div></td>
            <td><span class="badge" :class="ruleClass(r.status)">{{ r.status }}</span></td>
            <td>{{ threshold(r) }}</td>
            <td>{{ current(r) }}</td>
            <td style="font-size:11px;color:var(--text-muted)">{{ r.description }}</td>
          </tr>
        </tbody>
      </table>
    </template>
  </div>
</template>
<script setup lang="ts">
import { onMounted } from "vue"
import { useFetch } from "../composables/useFetch"
interface Rule { rule_id: string; name: string; description: string; status: string; active: boolean; threshold_try?: number; current_value_try?: number; threshold_pct?: number; current_max_pct?: number; threshold?: number; current?: number; blocked_adapter_ids?: string[] }
interface PolicyResp { rules: Rule[]; kill_switch_active: boolean }
const { data, loading, error, execute: load } = useFetch<PolicyResp>("/api/policy")
onMounted(load)
function ruleClass(s: string) { if (s === "OK") return "ok"; if (s === "ACTIVE" || s === "INACTIVE") return "info"; return "warn" }
function threshold(r: Rule) {
  if (r.threshold_try !== undefined) return `${r.threshold_try} ₺`
  if (r.threshold_pct !== undefined) return `${(r.threshold_pct * 100).toFixed(0)}%`
  if (r.threshold !== undefined) return r.threshold
  return "—"
}
function current(r: Rule) {
  if (r.current_value_try !== undefined) return `${r.current_value_try} ₺`
  if (r.current_max_pct !== undefined) return `${(r.current_max_pct * 100).toFixed(0)}%`
  if (r.current !== undefined) return r.current
  if (r.blocked_adapter_ids) return r.blocked_adapter_ids.join(", ") || "None"
  return "—"
}
</script>
<style scoped>.mono { font-family: monospace; }</style>
