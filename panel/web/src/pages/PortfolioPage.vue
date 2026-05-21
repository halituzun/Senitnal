<template>
  <div class="page">
    <div class="page-header">
      <div>
        <div class="page-title">Strategy Portfolio</div>
        <div class="page-subtitle">Live production strategy lifecycle &amp; allocation</div>
      </div>
      <button @click="loadAll">Refresh</button>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error-msg">{{ error }}</div>

    <template v-else-if="portfolio">
      <div class="summary-grid">
        <div class="summary-card">
          <div class="summary-label">Capital</div>
          <div class="summary-value">{{ portfolio.total_allocated_try.toLocaleString() }} / {{ portfolio.approved_capital_value.toLocaleString() }} TRY</div>
          <div class="summary-sub">{{ ((portfolio.total_allocated_try / portfolio.approved_capital_value) * 100).toFixed(1) }}% allocated</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">Active Strategies</div>
          <div class="summary-value">{{ portfolio.active_strategy_count }}</div>
          <div class="summary-sub">{{ portfolio.paused_strategy_count }} paused</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">Max Daily Loss</div>
          <div class="summary-value">{{ portfolio.max_total_daily_loss_try.toLocaleString() }} TRY</div>
          <div class="summary-sub">{{ portfolio.max_open_orders }} max open orders</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">Kill Switch</div>
          <div class="summary-value" :class="portfolio.kill_switch_active ? 'error-text' : 'ok-text'">{{ portfolio.kill_switch_active ? "ACTIVE" : "Inactive" }}</div>
          <div class="summary-sub">Max correlation {{ portfolio.max_strategy_correlation }}</div>
        </div>
      </div>

      <div style="margin-top:24px">
        <div class="section-header">
          <div class="section-title">Strategies</div>
          <div class="filter-row">
            <select v-model="lifecycleFilter" @change="loadStrategies">
              <option value="">All States</option>
              <option value="ACTIVE_LIVE">Active Live</option>
              <option value="LIMITED_LIVE">Limited Live</option>
              <option value="PAUSED">Paused</option>
              <option value="ROLLBACK_REQUIRED">Rollback Required</option>
            </select>
            <select v-model="enabledFilter" @change="loadStrategies">
              <option value="">All</option>
              <option value="true">Enabled</option>
              <option value="false">Disabled</option>
            </select>
          </div>
        </div>

        <table v-if="strategies">
          <thead>
            <tr>
              <th>Strategy</th>
              <th>Lifecycle</th>
              <th>Allocated (TRY)</th>
              <th>Edge</th>
              <th>Risk</th>
              <th>Confidence</th>
              <th>Quality</th>
              <th>P&L Today</th>
              <th>P&L Week</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in strategies" :key="s.strategy_id">
              <td>
                <div style="font-weight:600">{{ s.name }}</div>
                <div class="mono" style="font-size:10px;color:var(--text-muted)">{{ s.strategy_id }}</div>
              </td>
              <td><span class="badge" :class="lifecycleBadge(s.lifecycle_state)">{{ s.lifecycle_state.replace("_", " ") }}</span></td>
              <td class="mono">{{ s.allocated_budget_try.toLocaleString() }}</td>
              <td :class="scoreColor(s.current_edge_score)">{{ s.current_edge_score.toFixed(2) }}</td>
              <td :class="scoreColor(1 - s.current_risk_score)">{{ s.current_risk_score.toFixed(2) }}</td>
              <td :class="scoreColor(s.current_confidence)">{{ s.current_confidence.toFixed(2) }}</td>
              <td :class="scoreColor(s.strategy_quality)">{{ s.strategy_quality.toFixed(2) }}</td>
              <td :class="pnlColor(s.pnl_today_try)">{{ s.pnl_today_try > 0 ? "+" : "" }}{{ s.pnl_today_try.toFixed(1) }}</td>
              <td :class="pnlColor(s.pnl_week_try)">{{ s.pnl_week_try > 0 ? "+" : "" }}{{ s.pnl_week_try.toFixed(1) }}</td>
            </tr>
          </tbody>
        </table>
        <div v-if="strategies" style="margin-top:8px;font-size:11px;color:var(--text-muted)">{{ strategies.length }} strategies</div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
import { useFetch } from "../composables/useFetch"

interface Strategy {
  strategy_id: string; name: string; lifecycle_state: string
  allocated_budget_try: number; max_entry_try: number; max_trades_per_day: number
  current_edge_score: number; current_risk_score: number; current_confidence: number
  enabled: boolean; strategy_quality: number
  pnl_today_try: number; pnl_week_try: number
}

interface PortfolioConfig {
  portfolio_id: string; approved_capital_mode: string; approved_capital_value: number
  total_allocated_try: number; max_total_daily_loss_try: number
  max_open_orders: number; max_strategy_correlation: number
  max_single_strategy_exposure: number; max_single_exchange_exposure: number
  kill_switch_active: boolean; active_strategy_count: number; paused_strategy_count: number
}

const lifecycleFilter = ref("")
const enabledFilter = ref("")

const { data: portfolio, loading, error, execute: loadPortfolio } = useFetch<PortfolioConfig>("/api/portfolio")
const strategies = ref<Strategy[]>([])

async function loadStrategies() {
  const params = new URLSearchParams()
  if (lifecycleFilter.value) params.set("lifecycle_state", lifecycleFilter.value)
  if (enabledFilter.value) params.set("enabled", enabledFilter.value)
  const qs = params.toString()
  const url = qs ? `/api/strategies?${qs}` : "/api/strategies"
  try {
    const res = await fetch(url, { credentials: "include" })
    if (res.ok) {
      const body = (await res.json()) as { strategies: Strategy[] }
      strategies.value = body.strategies
    }
  } catch { /* keep previous data */ }
}

async function loadAll() {
  await Promise.all([loadPortfolio(), loadStrategies()])
}

onMounted(loadAll)

function lifecycleBadge(s: string) {
  if (s === "ACTIVE_LIVE") return "ok"
  if (s === "LIMITED_LIVE") return "warn"
  if (s === "ROLLBACK_REQUIRED") return "error"
  return ""
}

function scoreColor(v: number) {
  if (v >= 0.7) return "ok-text"
  if (v >= 0.4) return "warn-text"
  return "error-text"
}

function pnlColor(v: number) {
  if (v > 0) return "ok-text"
  if (v < 0) return "error-text"
  return ""
}
</script>

<style scoped>
.summary-grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:12px; }
.summary-card { background: var(--bg2); border:1px solid var(--border); border-radius:8px; padding:14px 16px; }
.summary-label { font-size:11px; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px; }
.summary-value { font-size:20px; font-weight:700; }
.summary-sub { font-size:11px; color:var(--text-muted); margin-top:2px; }
.section-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:12px; }
.section-title { font-size:15px; font-weight:600; }
.filter-row { display:flex; gap:8px; }
.filter-row select { font-size:12px; padding:4px 8px; background:var(--bg2); color:var(--text); border:1px solid var(--border); border-radius:4px; }
.ok-text { color: var(--success); }
.warn-text { color: var(--warn); }
.error-text { color: var(--error); }
.mono { font-family: monospace; }
</style>
