<template>
  <div class="page">
    <div class="page-header">
      <div><div class="page-title">System Health</div><div class="page-subtitle">Service and adapter health status</div></div>
      <button @click="load">Refresh</button>
    </div>
    <div v-if="loading" class="loading">Loading…</div>
    <div v-else-if="error" class="error-msg">{{ error }}</div>
    <template v-else-if="data">
      <div class="stat-grid">
        <div class="stat-card" v-for="(svc, key) in data.services" :key="key">
          <div class="stat-label">{{ key }}</div>
          <div class="stat-value" :class="svc.status === 'OK' ? 'ok' : 'error'">{{ svc.status }}</div>
          <div style="font-size:11px;color:var(--text-muted);margin-top:4px">{{ svc.latency_ms }}ms</div>
        </div>
      </div>
      <div class="section-header">Adapters</div>
      <div class="stat-grid">
        <div class="stat-card"><div class="stat-label">Total</div><div class="stat-value">{{ data.adapters.total }}</div></div>
        <div class="stat-card"><div class="stat-label">Healthy</div><div class="stat-value ok">{{ data.adapters.healthy }}</div></div>
        <div class="stat-card"><div class="stat-label">Degraded</div><div class="stat-value" :class="data.adapters.degraded ? 'warn' : 'ok'">{{ data.adapters.degraded ? "Yes" : "No" }}</div></div>
      </div>
      <div class="section-header">Strategies</div>
      <div class="stat-grid">
        <div class="stat-card"><div class="stat-label">Active</div><div class="stat-value ok">{{ data.portfolio.active_strategies }}</div></div>
        <div class="stat-card"><div class="stat-label">Paused</div><div class="stat-value warn">{{ data.portfolio.paused_strategies }}</div></div>
        <div class="stat-card"><div class="stat-label">Rollback Required</div><div class="stat-value" :class="data.portfolio.rollback_required > 0 ? 'error' : 'ok'">{{ data.portfolio.rollback_required }}</div></div>
      </div>
    </template>
  </div>
</template>
<script setup lang="ts">
import { onMounted } from "vue"
import { useFetch } from "@/composables/useFetch.js"
interface HealthResp {
  status: string
  services: Record<string, { status: string; latency_ms: number }>
  adapters: { total: number; healthy: number; degraded: boolean }
  portfolio: { active_strategies: number; paused_strategies: number; rollback_required: number }
}
const { data, loading, error, execute: load } = useFetch<HealthResp>("/api/health")
onMounted(load)
</script>
<style scoped>.section-header { font-size:13px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:.05em;margin:20px 0 10px; }</style>
