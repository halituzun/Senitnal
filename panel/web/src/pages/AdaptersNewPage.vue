<template>
  <div class="page">
    <div class="page-header">
      <div>
        <div class="page-title">Register New Adapter</div>
        <div class="page-subtitle">Add a new intelligence adapter to the hub</div>
      </div>
      <router-link to="/adapters"><button>← Back</button></router-link>
    </div>

    <div class="card" style="max-width:560px">
      <form @submit.prevent="handleSubmit">
        <div class="field">
          <label>Adapter ID *</label>
          <input v-model="form.adapter_id" placeholder="my-adapter-v1" required />
          <div class="hint">Lowercase, hyphens only. Cannot be changed after registration.</div>
        </div>
        <div class="field">
          <label>Display Name *</label>
          <input v-model="form.name" placeholder="My Adapter" required />
        </div>
        <div class="field">
          <label>Source Family *</label>
          <select v-model="form.source_family" required>
            <option value="">Select…</option>
            <option value="TECHNICAL">Technical Analysis</option>
            <option value="NEWS">News</option>
            <option value="SOCIAL">Social Media</option>
            <option value="ONCHAIN">On-Chain</option>
            <option value="DERIVATIVES">Derivatives</option>
            <option value="MARKET_DATA">Market Data</option>
            <option value="SENTIMENT">Sentiment</option>
            <option value="RESEARCH">Research</option>
          </select>
        </div>
        <div class="field">
          <label>Initial Trust Band</label>
          <select v-model="form.trust_band">
            <option value="PROVISIONAL">Provisional (recommended for new adapters)</option>
            <option value="TRUSTED">Trusted</option>
          </select>
        </div>
        <div class="field">
          <label>Description</label>
          <input v-model="form.description" placeholder="Brief description of signal source" />
        </div>
        <div class="field">
          <label>Credential Reference ID (optional)</label>
          <input v-model="form.credential_ref_id" placeholder="cred-my-adapter" />
        </div>

        <div class="notice">
          <strong>Note:</strong> New adapters start in PROVISIONAL trust band and require validation before being elevated to TRUSTED.
          Trade and withdrawal access are always disabled for all adapters.
        </div>

        <div style="display:flex;gap:8px;margin-top:16px">
          <button type="submit" class="primary" :disabled="submitting">
            {{ submitting ? "Registering…" : "Register Adapter" }}
          </button>
          <router-link to="/adapters"><button type="button">Cancel</button></router-link>
        </div>

        <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
        <div v-if="success" class="success-msg">✓ Adapter <code>{{ success.adapter_id }}</code> registered. Visible in Adapters list.</div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue"

const form = reactive({
  adapter_id: "",
  name: "",
  source_family: "",
  trust_band: "PROVISIONAL",
  description: "",
  credential_ref_id: "",
})
const submitting = ref(false)
const success = ref<{ adapter_id: string } | null>(null)
const errorMsg = ref("")

async function handleSubmit() {
  submitting.value = true
  success.value = null
  errorMsg.value = ""
  try {
    const body: Record<string, unknown> = {
      adapter_id: form.adapter_id,
      name: form.name,
      source_family: form.source_family,
      trust_band: form.trust_band,
    }
    if (form.description) body["description"] = form.description
    if (form.credential_ref_id) body["credential_ref_id"] = form.credential_ref_id

    const res = await fetch("/api/adapters", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(body),
    })
    if (res.ok) {
      success.value = (await res.json()) as { adapter_id: string }
      form.adapter_id = ""
      form.name = ""
      form.description = ""
      form.credential_ref_id = ""
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
.success-msg { margin-top:12px; color:var(--success); font-size:13px; }
</style>
