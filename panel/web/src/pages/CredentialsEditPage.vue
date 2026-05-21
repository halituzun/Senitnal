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
            data-1p-ignore="true" readonly @focus="(e) => (e.target as HTMLInputElement).removeAttribute('readonly')"
          />
          <div class="hint">Leave blank to keep current.</div>
        </div>

        <!-- HMAC: needs both API Key (public) + Secret Key (private) -->
        <template v-if="cred.kind === 'hmac_secret'">
          <div class="field">
            <label>API Key *</label>
            <input
              v-model="hmac.api_key"
              type="text"
              placeholder="paste API Key here (public identifier)"
              required
              minlength="8"
              name="hmac_api_key_input"
              autocomplete="off"
              data-lpignore="true"
              data-1p-ignore="true" readonly @focus="(e) => (e.target as HTMLInputElement).removeAttribute('readonly')"
            />
            <div class="hint">Public part of the HMAC pair — sent in request headers.</div>
          </div>
          <div class="field">
            <label>Secret Key *</label>
            <input
              v-model="hmac.secret_key"
              type="text"
              placeholder="paste Secret Key here (private — used to sign requests)"
              required
              minlength="8"
              name="hmac_secret_key_input"
              autocomplete="off"
              data-lpignore="true"
              data-1p-ignore="true" readonly @focus="(e) => (e.target as HTMLInputElement).removeAttribute('readonly')"
            />
            <div class="hint">Private part — never sent on the wire, only used to sign locally. Encrypted with AES-256-GCM at rest.</div>
          </div>
        </template>

        <!-- OAuth2: needs Client ID + Client Secret -->
        <template v-else-if="cred.kind === 'oauth2_client'">
          <div class="field">
            <label>Client ID *</label>
            <input v-model="oauth.client_id" type="text" placeholder="paste OAuth2 Client ID" required minlength="4" name="oauth_id" autocomplete="off" data-lpignore="true" data-1p-ignore="true" readonly @focus="(e) => (e.target as HTMLInputElement).removeAttribute('readonly')" />
          </div>
          <div class="field">
            <label>Client Secret *</label>
            <input v-model="oauth.client_secret" type="text" placeholder="paste OAuth2 Client Secret" required minlength="8" name="oauth_secret" autocomplete="off" data-lpignore="true" data-1p-ignore="true" readonly @focus="(e) => (e.target as HTMLInputElement).removeAttribute('readonly')" />
          </div>
        </template>

        <!-- Single-string kinds (api_key, bearer_token) -->
        <div v-else class="field">
          <label>New {{ cred.kind === 'bearer_token' ? 'Token' : 'API Key' }} *</label>
          <input
            v-model="form.secret"
            type="text"
            :placeholder="cred.kind === 'bearer_token' ? 'paste your bearer token' : 'paste your API key'"
            required
            minlength="8"
            name="cred_edit_secret"
            autocomplete="off"
            data-lpignore="true"
            data-1p-ignore="true" readonly @focus="(e) => (e.target as HTMLInputElement).removeAttribute('readonly')"
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
const hmac = reactive({ api_key: "", secret_key: "" })
const oauth = reactive({ client_id: "", client_secret: "" })
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

  let secretPayload: string
  if (cred.value?.kind === "hmac_secret") {
    if (!hmac.api_key || !hmac.secret_key) {
      errorMsg.value = "Both API Key and Secret Key are required for HMAC"
      submitting.value = false
      return
    }
    secretPayload = JSON.stringify({ api_key: hmac.api_key, secret_key: hmac.secret_key })
  } else if (cred.value?.kind === "oauth2_client") {
    if (!oauth.client_id || !oauth.client_secret) {
      errorMsg.value = "Both Client ID and Client Secret are required for OAuth2"
      submitting.value = false
      return
    }
    secretPayload = JSON.stringify({ client_id: oauth.client_id, client_secret: oauth.client_secret })
  } else {
    secretPayload = form.secret
  }

  try {
    const body: Record<string, unknown> = { secret: secretPayload }
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
      hmac.api_key = ""
      hmac.secret_key = ""
      oauth.client_id = ""
      oauth.client_secret = ""
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
