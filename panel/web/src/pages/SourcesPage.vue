<template>
  <div class="page">
    <div class="page-header">
      <div><div class="page-title">Intelligence Sources</div><div class="page-subtitle">Signal source family overview</div></div>
      <button @click="load">Refresh</button>
    </div>
    <div v-if="loading" class="loading">Loading…</div>
    <div v-else-if="error" class="error-msg">{{ error }}</div>
    <table v-else-if="data">
      <thead><tr><th>Source Family</th><th>Adapters</th><th>Active</th><th>Healthy</th><th>Avg Error Rate</th></tr></thead>
      <tbody>
        <tr v-for="s in data.sources" :key="s.source_family">
          <td><span class="badge info">{{ s.source_family }}</span></td>
          <td>{{ s.adapter_count }}</td>
          <td>{{ s.active_count }}</td>
          <td :class="s.healthy_count < s.active_count ? 'warn-text' : 'ok-text'">{{ s.healthy_count }}</td>
          <td :class="(s.avg_error_rate * 100) > 5 ? 'warn-text' : ''">{{ (s.avg_error_rate * 100).toFixed(1) }}%</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
<script setup lang="ts">
import { onMounted } from "vue"
import { useFetch } from "@/composables/useFetch.js"
interface Source { source_family: string; adapter_count: number; active_count: number; healthy_count: number; avg_error_rate: number }
const { data, loading, error, execute: load } = useFetch<{ sources: Source[] }>("/api/sources")
onMounted(load)
</script>
<style scoped>
.ok-text { color: var(--success); }
.warn-text { color: var(--warn); }
</style>
