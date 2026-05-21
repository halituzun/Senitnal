<template>
  <div class="page">
    <div class="page-header">
      <div>
        <div class="page-title">Credential Vault</div>
        <div class="page-subtitle">{{ data?.total ?? 0 }} credentials — secrets never shown in full</div>
      </div>
      <div style="display:flex;gap:8px">
        <button @click="load">Refresh</button>
        <router-link to="/credentials/new"><button class="primary">+ Add Credential</button></router-link>
      </div>
    </div>

    <div v-if="expiring?.total && expiring.total > 0" class="expiry-banner">
      ⚠ {{ expiring.total }} credential(s) expiring within 30 days
    </div>

    <div class="filters">
      <select v-model="filters.kind" @change="load">
        <option value="">All kinds</option>
        <option value="api_key">API Key</option>
        <option value="hmac_secret">HMAC Secret</option>
        <option value="bearer_token">Bearer Token</option>
        <option value="oauth2_client">OAuth2 Client</option>
      </select>
      <select v-model="filters.active" @change="load">
        <option value="">All status</option>
        <option value="true">Active</option>
        <option value="false">Inactive</option>
      </select>
      <button @click="clearFilters">Clear</button>
    </div>

    <div v-if="loading" class="loading">Loading…</div>
    <div v-else-if="error" class="error-msg">{{ error }}</div>
    <table v-else-if="data">
      <thead>
        <tr>
          <th>Label</th>
          <th>Adapter</th>
          <th>Kind</th>
          <th>Secret</th>
          <th>Status</th>
          <th>Expires</th>
          <th>Flags</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="c in data.credentials" :key="c.ref_id">
          <td>
            <div style="font-weight:500">{{ c.label }}</div>
            <div style="font-size:11px;color:var(--text-muted);font-family:monospace">
              {{ c.ref_id }}
              <span v-if="c.source === 'user'" class="badge info" style="margin-left:6px">user-added</span>
            </div>
          </td>
          <td class="mono" style="font-size:11px">{{ c.adapter_id ?? "—" }}</td>
          <td><span class="badge info">{{ c.kind }}</span></td>
          <td class="mono" style="font-size:11px;color:var(--text-muted)">{{ c.masked_secret }}</td>
          <td><span class="badge" :class="c.is_active ? 'ok' : 'error'">{{ c.is_active ? "Active" : "Inactive" }}</span></td>
          <td :class="isExpiringSoon(c.expires_at_ms) ? 'warn-text' : ''">
            {{ c.expires_at_ms ? expiryLabel(c.expires_at_ms) : "Never" }}
          </td>
          <td style="font-size:11px;color:var(--text-muted)">
            read-only · no-trade · no-withdraw
          </td>
          <td style="white-space:nowrap">
            <router-link :to="`/credentials/${c.ref_id}/edit`" v-if="c.is_active">
              <button style="font-size:11px;padding:3px 8px;margin-right:4px">Edit</button>
            </router-link>
            <button
              v-if="c.is_active && (c.source === 'user' || c.overridden)"
              @click="deleteCred(c.ref_id, c.source === 'seed')"
              :disabled="deleting === c.ref_id"
              style="font-size:11px;padding:3px 8px;color:var(--error)"
            >
              {{ deleting === c.ref_id ? "…" : (c.source === "seed" ? "Revert" : "Delete") }}
            </button>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-else class="empty">No credentials found</div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from "vue"
import { useFetch } from "@/composables/useFetch.js"

interface Cred { ref_id: string; kind: string; adapter_id: string | null; label: string; masked_secret: string; trade_enabled: boolean; withdraw_enabled: boolean; read_only: boolean; created_at_ms: number; expires_at_ms: number | null; is_active: boolean; source: "seed" | "user"; overridden?: boolean }
interface CredsResponse { credentials: Cred[]; total: number }
interface ExpiringResponse { expiring: Array<{ ref_id: string; days_remaining: number }>; total: number }

const filters = reactive({ kind: "", active: "" })
const { data, loading, error, execute } = useFetch<CredsResponse>("")
const expiring = ref<ExpiringResponse | null>(null)
const deleting = ref<string | null>(null)

async function deleteCred(refId: string, isSeedRevert = false) {
  const msg = isSeedRevert
    ? `Revert credential ${refId} to its seed value? Your override will be removed.`
    : `Delete credential ${refId}? This marks it inactive.`
  if (!confirm(msg)) return
  deleting.value = refId
  try {
    const res = await fetch(`/api/credentials/${refId}`, { method: "DELETE", credentials: "include" })
    if (res.ok) {
      load()
    } else {
      const err = (await res.json()) as { error?: string }
      alert(err.error ?? `HTTP ${res.status}`)
    }
  } finally {
    deleting.value = null
  }
}

function buildUrl() {
  const p = new URLSearchParams()
  if (filters.kind) p.set("kind", filters.kind)
  if (filters.active) p.set("active", filters.active)
  return `/api/credentials?${p}`
}
function load() { execute(buildUrl()) }
function clearFilters() { filters.kind = ""; filters.active = ""; load() }

onMounted(async () => {
  load()
  const r = await fetch("/api/credentials/expiring-soon", { credentials: "include" })
  if (r.ok) expiring.value = (await r.json()) as ExpiringResponse
})

function isExpiringSoon(ms: number | null) {
  if (ms === null) return false
  return ms - Date.now() < 30 * 86_400_000
}
function expiryLabel(ms: number) {
  const days = Math.ceil((ms - Date.now()) / 86_400_000)
  if (days < 0) return "Expired"
  if (days === 0) return "Today"
  return `${days}d`
}
</script>

<style scoped>
.mono { font-family: monospace; font-size: 12px; }
.warn-text { color: var(--warn); }
.expiry-banner { background: #3a2a00; border: 1px solid var(--warn); color: var(--warn); border-radius: var(--radius); padding: 10px 16px; margin-bottom: 16px; font-size: 13px; }
</style>
