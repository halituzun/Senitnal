<template>
  <div class="page">
    <div class="page-header">
      <div><div class="page-title">Ideas</div><div class="page-subtitle">Improvement backlog</div></div>
      <button @click="load">Refresh</button>
    </div>
    <div class="filters">
      <select v-model="filters.status" @change="load">
        <option value="">All status</option>
        <option value="BACKLOG">Backlog</option>
        <option value="UNDER_REVIEW">Under Review</option>
        <option value="IN_PROGRESS">In Progress</option>
        <option value="DONE">Done</option>
      </select>
      <select v-model="filters.priority" @change="load">
        <option value="">All priorities</option>
        <option value="HIGH">High</option>
        <option value="MEDIUM">Medium</option>
        <option value="LOW">Low</option>
      </select>
    </div>
    <div v-if="loading" class="loading">Loading…</div>
    <div v-else-if="error" class="error-msg">{{ error }}</div>
    <div v-else-if="data" class="ideas-list">
      <div class="idea-card card" v-for="idea in data.ideas" :key="idea.idea_id">
        <div class="idea-header">
          <span style="font-weight:600">{{ idea.title }}</span>
          <span class="badge" :class="priorityClass(idea.priority)">{{ idea.priority }}</span>
          <span class="badge" :class="statusClass(idea.status)">{{ idea.status }}</span>
        </div>
        <div class="idea-desc">{{ idea.description }}</div>
        <div class="idea-tags">
          <span v-for="tag in idea.tags" :key="tag" class="tag">{{ tag }}</span>
        </div>
      </div>
      <div v-if="data.ideas.length === 0" class="empty">No ideas found</div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { reactive, onMounted } from "vue"
import { useFetch } from "../composables/useFetch"
interface Idea { idea_id: string; title: string; description: string; status: string; priority: string; tags: string[] }
const filters = reactive({ status: "", priority: "" })
const { data, loading, error, execute } = useFetch<{ ideas: Idea[] }>("")
function load() {
  const p = new URLSearchParams()
  if (filters.status) p.set("status", filters.status)
  if (filters.priority) p.set("priority", filters.priority)
  execute(`/api/ideas?${p}`)
}
onMounted(load)
function priorityClass(p: string) { return p === "HIGH" ? "error" : p === "MEDIUM" ? "warn" : "info" }
function statusClass(s: string) { return s === "DONE" ? "ok" : s === "IN_PROGRESS" ? "warn" : "info" }
</script>
<style scoped>
.ideas-list { display:flex; flex-direction:column; gap:12px; }
.idea-card { padding:16px; }
.idea-header { display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin-bottom:8px; }
.idea-desc { font-size:13px; color:var(--text-muted); margin-bottom:8px; }
.idea-tags { display:flex; gap:6px; flex-wrap:wrap; }
.tag { background:var(--bg3); border:1px solid var(--border); border-radius:10px; padding:2px 8px; font-size:11px; color:var(--text-muted); }
</style>
