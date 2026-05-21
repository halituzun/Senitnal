<template>
  <div class="page">
    <div class="page-header">
      <div>
        <div class="page-title">Dashboard</div>
        <div class="page-subtitle">Portfolio and system overview</div>
      </div>
      <button @click="load">Refresh</button>
    </div>

    <div v-if="loading" class="loading">Loading…</div>
    <div v-else-if="error" class="error-msg">{{ error }}</div>
    <template v-else-if="data">
      <!-- Portfolio stats -->
      <div class="stat-grid">
        <div class="stat-card">
          <div class="stat-label">Approved Capital</div>
          <div class="stat-value">{{ fmt(data.portfolio.approved_capital_value) }} ₺</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Allocated</div>
          <div class="stat-value">{{ fmt(data.portfolio.total_allocated_try) }} ₺</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Utilization</div>
          <div class="stat-value">{{ pct(data.portfolio.total_allocated_try, data.portfolio.approved_capital_value) }}%</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Active Strategies</div>
          <div class="stat-value ok">{{ data.portfolio.active_strategy_count }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Paused</div>
          <div class="stat-value warn">{{ data.portfolio.paused_strategy_count }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Kill Switch</div>
          <div class="stat-value" :class="data.portfolio.kill_switch_active ? 'error' : 'ok'">
            {{ data.portfolio.kill_switch_active ? "ACTIVE" : "OFF" }}
          </div>
        </div>
      </div>

      <!-- PnL -->
      <div class="stat-grid">
        <div class="stat-card">
          <div class="stat-label">PnL Today</div>
          <div class="stat-value" :class="data.pnl_summary.today_try >= 0 ? 'ok' : 'error'">
            {{ data.pnl_summary.today_try >= 0 ? "+" : "" }}{{ fmt(data.pnl_summary.today_try) }} ₺
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-label">PnL This Week</div>
          <div class="stat-value" :class="data.pnl_summary.week_try >= 0 ? 'ok' : 'error'">
            {{ data.pnl_summary.week_try >= 0 ? "+" : "" }}{{ fmt(data.pnl_summary.week_try) }} ₺
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-label">PnL This Month</div>
          <div class="stat-value ok">+{{ fmt(data.pnl_summary.month_try) }} ₺</div>
        </div>
      </div>

      <!-- Adapter hub -->
      <div class="section-header">Adapter Hub</div>
      <div class="stat-grid">
        <div class="stat-card">
          <div class="stat-label">Total Adapters</div>
          <div class="stat-value">{{ data.adapter_hub.total_adapters }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Healthy</div>
          <div class="stat-value ok">{{ data.adapter_hub.healthy_count }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Stale</div>
          <div class="stat-value" :class="data.adapter_hub.stale_count > 0 ? 'warn' : 'ok'">{{ data.adapter_hub.stale_count }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Quarantined</div>
          <div class="stat-value" :class="data.adapter_hub.quarantined_count > 0 ? 'error' : 'ok'">{{ data.adapter_hub.quarantined_count }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Revoked</div>
          <div class="stat-value" :class="data.adapter_hub.revoked_count > 0 ? 'error' : 'ok'">{{ data.adapter_hub.revoked_count }}</div>
        </div>
      </div>

      <!-- Recent events -->
      <div class="section-header">Recent Events</div>
      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>Severity</th>
            <th>Type</th>
            <th>Message</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ev in data.recent_events" :key="ev.id">
            <td class="mono">{{ relTime(ev.ts_ms) }}</td>
            <td><span class="badge" :class="ev.severity.toLowerCase()">{{ ev.severity }}</span></td>
            <td class="mono" style="font-size:11px">{{ ev.event_type }}</td>
            <td style="color:var(--text-muted)">{{ ev.message }}</td>
          </tr>
        </tbody>
      </table>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from "vue"
import { useFetch } from "@/composables/useFetch.js"

interface Dashboard {
  portfolio: {
    approved_capital_value: number
    total_allocated_try: number
    active_strategy_count: number
    paused_strategy_count: number
    kill_switch_active: boolean
  }
  pnl_summary: { today_try: number; week_try: number; month_try: number }
  adapter_hub: { total_adapters: number; healthy_count: number; stale_count: number; quarantined_count: number; revoked_count: number; degraded: boolean }
  recent_events: Array<{ id: string; ts_ms: number; severity: string; event_type: string; message: string }>
  captured_at_ms: number
}

const { data, loading, error, execute: load } = useFetch<Dashboard>("/api/dashboard")

onMounted(load)

function fmt(v: number) { return v.toLocaleString("tr-TR", { minimumFractionDigits: 1, maximumFractionDigits: 1 }) }
function pct(a: number, b: number) { return b > 0 ? ((a / b) * 100).toFixed(1) : "0.0" }
function relTime(ms: number) {
  const diff = Date.now() - ms
  if (diff < 60_000) return `${Math.round(diff / 1000)}s ago`
  if (diff < 3_600_000) return `${Math.round(diff / 60_000)}m ago`
  return `${Math.round(diff / 3_600_000)}h ago`
}
</script>

<style scoped>
.section-header { font-size: 13px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin: 20px 0 10px; }
.mono { font-family: monospace; font-size: 12px; }
</style>
