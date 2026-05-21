<template>
  <div class="page">
    <div class="page-header">
      <div>
        <div class="page-title">Add Credential</div>
        <div class="page-subtitle">Secret encrypted at rest · never returned in any response</div>
      </div>
      <router-link to="/credentials"><button>← Back</button></router-link>
    </div>

    <div class="card" style="max-width:640px">
      <form @submit.prevent="handleSubmit" autocomplete="off">
        <div class="field">
          <label>Adapter ID *</label>
          <input v-model="form.adapter_id" placeholder="binance-spot-account" required name="adp_id" autocomplete="off" />
          <div class="hint">The adapter this credential belongs to (lowercase, hyphens).</div>
        </div>

        <div class="field">
          <label>Label *</label>
          <input v-model="form.label" placeholder="Binance Spot (read-only)" required name="cred_label" autocomplete="off" />
        </div>

        <div class="field">
          <label>Kind *</label>
          <select v-model="form.kind" required name="cred_kind">
            <option value="api_key">API Key</option>
            <option value="hmac_secret">HMAC Secret</option>
            <option value="bearer_token">Bearer Token</option>
            <option value="oauth2_client">OAuth2 Client</option>
          </select>
        </div>

        <div class="field">
          <label>Secret *</label>
          <input v-model="form.secret" type="text" placeholder="paste your API key here" required minlength="8" name="cred_secret_input" autocomplete="off" data-lpignore="true" data-1p-ignore="true" />
          <div class="hint">
            Encrypted with AES-256-GCM before storage. Only a SHA256 fingerprint is shown afterwards.
            <strong>This panel can never trade or withdraw — flags hardcoded to false.</strong>
          </div>
        </div>

        <div class="field">
          <label>Expires (days from now, optional)</label>
          <input v-model.number="form.expires_days" type="number" min="1" max="3650" placeholder="365" name="cred_exp_days" autocomplete="off" />
        </div>

        <div class="notice">
          <strong>Security pinned by schema:</strong>
          <ul>
            <li><code>trade_enabled = false</code></li>
            <li><code>withdraw_enabled = false</code></li>
            <li><code>read_only = true</code></li>
          </ul>
          Even if the source API key has wider scopes, this panel can never act on them.
        </div>

        <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
        <div v-if="success" class="success-msg">
          ✓ Credential added: <code class="mono">{{ success.ref_id }}</code><br />
          Fingerprint: <code class="mono">{{ success.masked_secret }}</code>
        </div>

        <div style="display:flex;gap:8px;margin-top:16px">
          <button type="submit" class="primary" :disabled="submitting">
            {{ submitting ? "Encrypting…" : "Add Credential" }}
          </button>
          <router-link to="/credentials"><button type="button">Cancel</button></router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue"

const form = reactive({
  adapter_id: "",
  label: "",
  kind: "api_key",
  secret: "",
  expires_days: null as number | null,
})
const submitting = ref(false)
const errorMsg = ref("")
const success = ref<{ ref_id: string; masked_secret: string } | null>(null)

async function handleSubmit() {
  submitting.value = true
  errorMsg.value = ""
  success.value = null

  const expires_at_ms = form.expires_days ? Date.now() + form.expires_days * 86_400_000 : null

  try {
    const res = await fetch("/api/credentials", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({
        adapter_id: form.adapter_id,
        label: form.label,
        kind: form.kind,
        secret: form.secret,
        expires_at_ms,
      }),
    })
    if (res.ok) {
      const data = (await res.json()) as { ref_id: string; masked_secret: string }
      success.value = data
      // Clear secret immediately
      form.secret = ""
      form.adapter_id = ""
      form.label = ""
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
.field { margin-bottom: 16px; }
.field label { display:block; font-size:12px; font-weight:600; color:var(--text-muted); margin-bottom:5px; text-transform:uppercase; letter-spacing:0.04em; }
.field input, .field select { width:100%; }
.hint { font-size:11px; color:var(--text-muted); margin-top:4px; }
.notice { background:var(--bg3); border:1px solid var(--border); border-radius:var(--radius); padding:12px; font-size:12px; color:var(--text-muted); margin-top:8px; }
.notice ul { margin: 4px 0 0 18px; }
.notice code { background:var(--bg); padding:1px 4px; border-radius:3px; font-size:11px; }
.success-msg { margin-top:12px; color:var(--success); font-size:13px; background:#0e2a14; border:1px solid var(--success); border-radius:var(--radius); padding:12px; }
.mono { font-family: monospace; }
</style>
