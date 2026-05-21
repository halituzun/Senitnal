// Encrypted credential vault — SQLite + AES-256-GCM
// CRITICAL INVARIANTS:
//   - Plaintext secrets NEVER leave this module
//   - GET responses include only masked_secret (SHA256 fingerprint, no key material)
//   - trade_enabled / withdraw_enabled are pinned to 0 at schema level (CHECK constraint)
//   - read_only is pinned to 1 at schema level

import Database from "better-sqlite3"
import crypto from "node:crypto"
import path from "node:path"
import fs from "node:fs"

const DB_PATH = process.env["PANEL_VAULT_DB"] ?? (process.env["VITEST"] ? ":memory:" : path.join(process.cwd(), "vault.db"))

// Master key — from env, or ephemeral with warning
function loadMasterKey(): Buffer {
  const fromEnv = process.env["PANEL_VAULT_KEY"]
  if (fromEnv && /^[0-9a-f]{64}$/i.test(fromEnv)) {
    return Buffer.from(fromEnv, "hex")
  }
  if (fromEnv) {
    console.error("FATAL: PANEL_VAULT_KEY must be 64 hex chars (32 bytes)")
    process.exit(1)
  }
  const ephemeral = crypto.randomBytes(32)
  console.warn("")
  console.warn("⚠  PANEL_VAULT_KEY not set — using ephemeral key.")
  console.warn("   Credentials added now will be UNREADABLE after restart.")
  console.warn("   To persist, set this env var before next start:")
  console.warn(`   export PANEL_VAULT_KEY=${ephemeral.toString("hex")}`)
  console.warn("")
  return ephemeral
}

const MASTER_KEY = loadMasterKey()

const db = new Database(DB_PATH)
if (DB_PATH !== ":memory:") {
  db.pragma("journal_mode = WAL")
}
db.pragma("foreign_keys = ON")

// Schema with CHECK constraints enforcing read-only at DB level
db.exec(`
  CREATE TABLE IF NOT EXISTS user_credentials (
    ref_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    adapter_id TEXT NOT NULL,
    label TEXT NOT NULL,
    masked_secret TEXT NOT NULL,
    encrypted_secret BLOB NOT NULL,
    iv BLOB NOT NULL,
    auth_tag BLOB NOT NULL,
    created_at_ms INTEGER NOT NULL,
    expires_at_ms INTEGER,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    trade_enabled INTEGER NOT NULL DEFAULT 0 CHECK (trade_enabled = 0),
    withdraw_enabled INTEGER NOT NULL DEFAULT 0 CHECK (withdraw_enabled = 0),
    read_only INTEGER NOT NULL DEFAULT 1 CHECK (read_only = 1)
  );

  CREATE TABLE IF NOT EXISTS seed_overrides (
    ref_id TEXT PRIMARY KEY,
    label TEXT,
    expires_at_ms INTEGER,
    masked_secret TEXT NOT NULL,
    encrypted_secret BLOB NOT NULL,
    iv BLOB NOT NULL,
    auth_tag BLOB NOT NULL,
    updated_at_ms INTEGER NOT NULL,
    trade_enabled INTEGER NOT NULL DEFAULT 0 CHECK (trade_enabled = 0),
    withdraw_enabled INTEGER NOT NULL DEFAULT 0 CHECK (withdraw_enabled = 0),
    read_only INTEGER NOT NULL DEFAULT 1 CHECK (read_only = 1)
  );

  CREATE TABLE IF NOT EXISTS user_adapters (
    adapter_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    source_family TEXT NOT NULL,
    trust_band TEXT NOT NULL DEFAULT 'PROVISIONAL'
      CHECK (trust_band IN ('TRUSTED', 'PROVISIONAL', 'QUARANTINED', 'REVOKED')),
    description TEXT,
    credential_ref_id TEXT,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at_ms INTEGER NOT NULL
  );
`)

// ─── Encryption helpers ────────────────────────────────────────────────────────

function encrypt(plaintext: string): { ciphertext: Buffer; iv: Buffer; authTag: Buffer } {
  const iv = crypto.randomBytes(12)
  const cipher = crypto.createCipheriv("aes-256-gcm", MASTER_KEY, iv)
  const ciphertext = Buffer.concat([cipher.update(plaintext, "utf8"), cipher.final()])
  return { ciphertext, iv, authTag: cipher.getAuthTag() }
}

// Public mask: 4-hex SHA256 fingerprint, no plaintext material
function maskSecret(plaintext: string, kind: string): string {
  const fingerprint = crypto
    .createHash("sha256")
    .update(plaintext)
    .digest("hex")
    .slice(0, 4)
    .toUpperCase()
  const prefix = kind === "hmac_secret" ? "hmac" : kind === "bearer_token" ? "br" : kind === "oauth2_client" ? "oa2" : "key"
  return `${prefix}_${"•".repeat(16)}${fingerprint}`
}

// ─── Credential CRUD ───────────────────────────────────────────────────────────

export interface CredentialPublic {
  ref_id: string
  kind: string
  adapter_id: string
  label: string
  masked_secret: string
  created_at_ms: number
  expires_at_ms: number | null
  is_active: boolean
  trade_enabled: false
  withdraw_enabled: false
  read_only: true
}

interface CredentialRow {
  ref_id: string
  kind: string
  adapter_id: string
  label: string
  masked_secret: string
  created_at_ms: number
  expires_at_ms: number | null
  is_active: number
}

const insertCredStmt = db.prepare(`
  INSERT INTO user_credentials
    (ref_id, kind, adapter_id, label, masked_secret, encrypted_secret, iv, auth_tag,
     created_at_ms, expires_at_ms, is_active, trade_enabled, withdraw_enabled, read_only)
  VALUES
    (@ref_id, @kind, @adapter_id, @label, @masked_secret, @encrypted_secret, @iv, @auth_tag,
     @created_at_ms, @expires_at_ms, 1, 0, 0, 1)
`)

const listCredStmt = db.prepare(`
  SELECT ref_id, kind, adapter_id, label, masked_secret, created_at_ms, expires_at_ms, is_active
  FROM user_credentials
  ORDER BY created_at_ms DESC
`)

const getCredStmt = db.prepare(`
  SELECT ref_id, kind, adapter_id, label, masked_secret, created_at_ms, expires_at_ms, is_active
  FROM user_credentials
  WHERE ref_id = ?
`)

const deactivateCredStmt = db.prepare(`
  UPDATE user_credentials SET is_active = 0 WHERE ref_id = ?
`)

const VALID_KINDS = new Set(["api_key", "hmac_secret", "bearer_token", "oauth2_client"])

export function addCredential(input: {
  kind: string
  adapter_id: string
  label: string
  secret: string
  expires_at_ms: number | null
}): CredentialPublic {
  if (!VALID_KINDS.has(input.kind)) {
    throw new Error(`Invalid kind: ${input.kind}`)
  }
  if (input.secret.length < 8 || input.secret.length > 4096) {
    throw new Error("Secret must be 8-4096 chars")
  }
  const ref_id = `cred-user-${crypto.randomBytes(6).toString("hex")}`
  const { ciphertext, iv, authTag } = encrypt(input.secret)
  const masked_secret = maskSecret(input.secret, input.kind)
  const created_at_ms = Date.now()

  insertCredStmt.run({
    ref_id,
    kind: input.kind,
    adapter_id: input.adapter_id,
    label: input.label,
    masked_secret,
    encrypted_secret: ciphertext,
    iv,
    auth_tag: authTag,
    created_at_ms,
    expires_at_ms: input.expires_at_ms,
  })

  return rowToPublic({
    ref_id,
    kind: input.kind,
    adapter_id: input.adapter_id,
    label: input.label,
    masked_secret,
    created_at_ms,
    expires_at_ms: input.expires_at_ms,
    is_active: 1,
  })
}

export function listCredentials(): CredentialPublic[] {
  const rows = listCredStmt.all() as CredentialRow[]
  return rows.map(rowToPublic)
}

export function getCredential(ref_id: string): CredentialPublic | null {
  const row = getCredStmt.get(ref_id) as CredentialRow | undefined
  return row ? rowToPublic(row) : null
}

export function deactivateCredential(ref_id: string): boolean {
  const result = deactivateCredStmt.run(ref_id)
  return result.changes > 0
}

function rowToPublic(row: CredentialRow): CredentialPublic {
  return {
    ref_id: row.ref_id,
    kind: row.kind,
    adapter_id: row.adapter_id,
    label: row.label,
    masked_secret: row.masked_secret,
    created_at_ms: row.created_at_ms,
    expires_at_ms: row.expires_at_ms,
    is_active: row.is_active === 1,
    trade_enabled: false,
    withdraw_enabled: false,
    read_only: true,
  }
}

// ─── Seed override (Edit existing seed credential) ────────────────────────────

export interface SeedOverridePublic {
  ref_id: string
  label: string | null
  expires_at_ms: number | null
  masked_secret: string
  updated_at_ms: number
  trade_enabled: false
  withdraw_enabled: false
  read_only: true
}

const upsertOverrideStmt = db.prepare(`
  INSERT INTO seed_overrides
    (ref_id, label, expires_at_ms, masked_secret, encrypted_secret, iv, auth_tag, updated_at_ms,
     trade_enabled, withdraw_enabled, read_only)
  VALUES
    (@ref_id, @label, @expires_at_ms, @masked_secret, @encrypted_secret, @iv, @auth_tag, @updated_at_ms,
     0, 0, 1)
  ON CONFLICT(ref_id) DO UPDATE SET
    label = excluded.label,
    expires_at_ms = excluded.expires_at_ms,
    masked_secret = excluded.masked_secret,
    encrypted_secret = excluded.encrypted_secret,
    iv = excluded.iv,
    auth_tag = excluded.auth_tag,
    updated_at_ms = excluded.updated_at_ms
`)

const getOverrideStmt = db.prepare(`
  SELECT ref_id, label, expires_at_ms, masked_secret, updated_at_ms
  FROM seed_overrides
  WHERE ref_id = ?
`)

const listOverridesStmt = db.prepare(`
  SELECT ref_id, label, expires_at_ms, masked_secret, updated_at_ms
  FROM seed_overrides
`)

const clearOverrideStmt = db.prepare(`
  DELETE FROM seed_overrides WHERE ref_id = ?
`)

export function setSeedOverride(input: {
  ref_id: string
  kind: string
  secret: string
  label?: string
  expires_at_ms?: number | null
}): SeedOverridePublic {
  if (input.secret.length < 8 || input.secret.length > 4096) {
    throw new Error("Secret must be 8-4096 chars")
  }
  const { ciphertext, iv, authTag } = encrypt(input.secret)
  const masked_secret = maskSecret(input.secret, input.kind)
  const updated_at_ms = Date.now()

  upsertOverrideStmt.run({
    ref_id: input.ref_id,
    label: input.label ?? null,
    expires_at_ms: input.expires_at_ms ?? null,
    masked_secret,
    encrypted_secret: ciphertext,
    iv,
    auth_tag: authTag,
    updated_at_ms,
  })

  return {
    ref_id: input.ref_id,
    label: input.label ?? null,
    expires_at_ms: input.expires_at_ms ?? null,
    masked_secret,
    updated_at_ms,
    trade_enabled: false,
    withdraw_enabled: false,
    read_only: true,
  }
}

export function getSeedOverride(ref_id: string): SeedOverridePublic | null {
  const row = getOverrideStmt.get(ref_id) as
    | { ref_id: string; label: string | null; expires_at_ms: number | null; masked_secret: string; updated_at_ms: number }
    | undefined
  if (!row) return null
  return {
    ...row,
    trade_enabled: false,
    withdraw_enabled: false,
    read_only: true,
  }
}

export function listSeedOverrides(): Record<string, SeedOverridePublic> {
  const rows = listOverridesStmt.all() as Array<{
    ref_id: string; label: string | null; expires_at_ms: number | null; masked_secret: string; updated_at_ms: number
  }>
  const out: Record<string, SeedOverridePublic> = {}
  for (const r of rows) {
    out[r.ref_id] = { ...r, trade_enabled: false, withdraw_enabled: false, read_only: true }
  }
  return out
}

export function clearSeedOverride(ref_id: string): boolean {
  return clearOverrideStmt.run(ref_id).changes > 0
}

// ─── Adapter CRUD ──────────────────────────────────────────────────────────────

export interface AdapterPublic {
  adapter_id: string
  name: string
  source_family: string
  trust_band: string
  description: string | null
  credential_ref_id: string | null
  is_active: boolean
  created_at_ms: number
  is_user_added: true
}

interface AdapterRow {
  adapter_id: string
  name: string
  source_family: string
  trust_band: string
  description: string | null
  credential_ref_id: string | null
  is_active: number
  created_at_ms: number
}

const insertAdapterStmt = db.prepare(`
  INSERT INTO user_adapters
    (adapter_id, name, source_family, trust_band, description, credential_ref_id, is_active, created_at_ms)
  VALUES
    (@adapter_id, @name, @source_family, @trust_band, @description, @credential_ref_id, 1, @created_at_ms)
`)

const listAdaptersStmt = db.prepare(`
  SELECT adapter_id, name, source_family, trust_band, description, credential_ref_id, is_active, created_at_ms
  FROM user_adapters
  ORDER BY created_at_ms DESC
`)

const VALID_FAMILIES = new Set([
  "TECHNICAL", "NEWS", "SOCIAL", "ONCHAIN", "DERIVATIVES",
  "MARKET_DATA", "ACCOUNT_DATA", "SENTIMENT", "RESEARCH", "INFRASTRUCTURE",
])
const VALID_BANDS = new Set(["TRUSTED", "PROVISIONAL", "QUARANTINED", "REVOKED"])

export function addAdapter(input: {
  adapter_id: string
  name: string
  source_family: string
  trust_band?: string
  description?: string
  credential_ref_id?: string
}): AdapterPublic {
  if (!/^[a-z0-9][a-z0-9-]{1,63}$/.test(input.adapter_id)) {
    throw new Error("adapter_id must be lowercase, alphanumeric + hyphens, 2-64 chars")
  }
  if (!VALID_FAMILIES.has(input.source_family)) {
    throw new Error(`Invalid source_family: ${input.source_family}`)
  }
  const trust_band = input.trust_band ?? "PROVISIONAL"
  if (!VALID_BANDS.has(trust_band)) {
    throw new Error(`Invalid trust_band: ${trust_band}`)
  }
  const created_at_ms = Date.now()

  try {
    insertAdapterStmt.run({
      adapter_id: input.adapter_id,
      name: input.name,
      source_family: input.source_family,
      trust_band,
      description: input.description ?? null,
      credential_ref_id: input.credential_ref_id ?? null,
      created_at_ms,
    })
  } catch (e) {
    if (e instanceof Error && e.message.includes("UNIQUE")) {
      throw new Error(`Adapter ${input.adapter_id} already exists`)
    }
    throw e
  }

  return {
    adapter_id: input.adapter_id,
    name: input.name,
    source_family: input.source_family,
    trust_band,
    description: input.description ?? null,
    credential_ref_id: input.credential_ref_id ?? null,
    is_active: true,
    created_at_ms,
    is_user_added: true,
  }
}

export function listAdapters(): AdapterPublic[] {
  const rows = listAdaptersStmt.all() as AdapterRow[]
  return rows.map((r) => ({
    adapter_id: r.adapter_id,
    name: r.name,
    source_family: r.source_family,
    trust_band: r.trust_band,
    description: r.description,
    credential_ref_id: r.credential_ref_id,
    is_active: r.is_active === 1,
    created_at_ms: r.created_at_ms,
    is_user_added: true,
  }))
}

// Ensure DB is created and gitignored
if (!fs.existsSync(DB_PATH)) {
  fs.writeFileSync(DB_PATH, "")
  fs.unlinkSync(DB_PATH)
}
