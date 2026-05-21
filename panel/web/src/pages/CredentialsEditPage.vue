<template>
  <div class="page">
    <div class="page-header">
      <div>
        <div class="page-title">Edit Credential</div>
        <div class="page-subtitle">
          Paste a new secret · encrypted at rest · never returned anywhere
        </div>
      </div>
      <router-link to="/credentials"><button>← Back</button></router-link>
    </div>

    <div v-if="!cred" class="loading">Loading…</div>
    <div v-else class="card" style="max-width:640px">
      <div class="cur-info">
        <div class="row">
          <span class="muted">Ref ID:</span>
          <code class="mono">{{ cred.ref_id }}</code>
        </div>
        <div class="row">
          <span class="muted">Adapter:</span>
          <code class="mono">{{ cred.adapter_id }}</code>
          <span class="badge info" style="margin-left:6px">{{ cred.kind }}</span>
        </div>
        <div class="row">
          <span class="muted">Current secret:</span>
          <code class="mono">{{ cred.masked_secret }}</code>
          <span v-if="cred.overridden" class="badge warn" style="margin-left:6px">overridden</span>
        </div>
      </div>

      <form @submit.prevent="handleSubmit" autocomplete="off">
        <div class="field">
          <label>Label</label>
          <input
            v-model="form.label"
            :placeholder="cred.label"
            name="cred_edit_label"
            autocomplete="off"
            data-lpignore="true"
            data-1p-ignore="true"
          />
          <div class="hint">Leave blank to keep current.</div>
        </div>

        <div class="field">
          <label>New Secret *</label>
          <input
            v-model="form.secret"
            type="text"
            placeholder="paste your new API key here"
            required
            minlength="8"
            name="cred_edit_secret"
            autocomplete="off"
            data-lpignore="true"
            data-1p-ignore="true"
          />
          <div class="hint">
            <strong>Encrypted with AES-256-GCM.</strong> Only a SHA256 fingerprint is shown afterward.
            This panel can never trade or withdraw — flags hardcoded.
          </div>
        </div>

        <div class="field">
          <label>Expires (days from now)</label>
          <input v-model.number="form.expires_days" type="number" min="1" max="3650" placeholder="90" name="cred_edit_exp" autocomplete="off" />
          <div class="hint">Leave blank to inherit current expiry.</div>
        </div>

        <div class="notice">
          Locked by schema for this credential: <code>trade_enabled=false</code>,
          <code>withdraw_enabled=false</code>, <code>read_only=true</code>. Cannot be changed via API.
        </div>

        <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
        <div v-if="success" class="success-msg">
          ✓ Secret rotated. New fingerprint:
          <code class="mono">{{ success.masked_secret }}</code>
        </div>

        <div style="display:flex;gap:8px;margin-top:16px">
          <button type="submit" class="primary" :disabled="submitting">
            {{ submitting ? "Encrypting…" : "Save & Encrypt" }}
          </button>
          <router-link to="/credentials"><button type="button">Cancel</button></router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from "vue"
import { useRoute } from "vue-router"

const route = useRoute()
const refId = route.params["ref_id"] as string

interface Cred {
  ref_id: string
  kind: string
  adapter_id: string
  label: string
  masked_secret: string
  expires_at_ms: number | null
  source: "seed" | "user"
  overridden?: boolean
}

const cred = ref<Cred | null>(null)
const form = reactive({ label: "", secret: "", expires_days: null as number | null })
const submitting = ref(false)
const errorMsg = ref("")
const success = ref<{ masked_secret: string } | null>(null)

onMounted(async () => {
  const res = await fetch(`/api/credentials/${refId}`, { credentials: "include" })
  if (res.ok) {
    cred.value = (await res.json()) as Cred
  } else {
    errorMsg.value = "Failed to load credential"
  }
})

async function handleSubmit() {
  submitting.value = true
  errorMsg.value = ""
  success.value = null

  const expires_at_ms = form.expires_days ? Date.now() + form.expires_days * 86_400_000 : null

  try {
    const body: Record<string, unknown> = { secret: form.secret }
    if (form.label) body["label"] = form.label
    if (expires_at_ms !== null) body["expires_at_ms"] = expires_at_ms

    const res = await fetch(`/api/credentials/${refId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(body),
    })
    if (res.ok) {
      const data = (await res.json()) as { masked_secret: string }
      success.value = data
      form.secret = ""
      // Reload current state
      const cur = await fetch(`/api/credentials/${refId}`, { credentials: "include" })
      if (cur.ok) cred.value = (await cur.json()) as Cred
    } else {
      const err = (await res.json()) as { error?: string }
      errorMsg.value = err.error ?? `HTTP ${res.status}`
    }
  } catch (e) {
    errorMsg.value = e instanceof Error ? e.message : "Network error"
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.cur-info { background: var(--bg3); border: 1px solid var(--border); border-radius: var(--radius); padding: 12px 14px; margin-bottom: 16px; font-size: 12px; }
.cur-info .row { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.cur-info .muted { color: var(--text-muted); min-width: 100px; }
.field { margin-bottom: 16px; }
.field label { display:block; font-size:12px; font-weight:600; color:var(--text-muted); margin-bottom:5px; text-transform:uppercase; letter-spacing:0.04em; }
.field input { width:100%; }
.hint { font-size:11px; color:var(--text-muted); margin-top:4px; }
.notice { background:var(--bg3); border:1px solid var(--border); border-radius:var(--radius); padding:10px 12px; font-size:11px; color:var(--text-muted); }
.notice code { background:var(--bg); padding:1px 4px; border-radius:3px; font-size:11px; }
.success-msg { margin-top:12px; color:var(--success); font-size:13px; background:#0e2a14; border:1px solid var(--success); border-radius:var(--radius); padding:12px; }
.mono { font-family: monospace; font-size: 12px; }
</style>
