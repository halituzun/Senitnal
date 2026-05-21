// Credential routes — NEVER returns full secrets, only masked_secret
import type { FastifyInstance } from "fastify"
import { requireAuth } from "../auth.js"
import { CREDENTIALS } from "../mock/data.js"
import {
  addCredential, listCredentials, getCredential, deactivateCredential,
  setSeedOverride, listSeedOverrides, clearSeedOverride,
} from "../db/vault.js"

interface SafeCred {
  ref_id: string
  kind: string
  adapter_id: string | null
  label: string
  masked_secret: string
  created_at_ms: number
  expires_at_ms: number | null
  is_active: boolean
  trade_enabled: false
  withdraw_enabled: false
  read_only: true
  source: "seed" | "user"
  overridden?: boolean
  updated_at_ms?: number
}

function allCredentials(): SafeCred[] {
  const overrides = listSeedOverrides()
  const seed: SafeCred[] = CREDENTIALS.map((c) => {
    const ov = overrides[c.ref_id]
    if (ov) {
      return {
        ref_id: c.ref_id,
        kind: c.kind,
        adapter_id: c.adapter_id,
        label: ov.label ?? c.label,
        masked_secret: ov.masked_secret,
        created_at_ms: c.created_at_ms,
        expires_at_ms: ov.expires_at_ms ?? c.expires_at_ms,
        is_active: c.is_active,
        trade_enabled: false,
        withdraw_enabled: false,
        read_only: true,
        source: "seed" as const,
        overridden: true,
        updated_at_ms: ov.updated_at_ms,
      }
    }
    return {
      ref_id: c.ref_id,
      kind: c.kind,
      adapter_id: c.adapter_id,
      label: c.label,
      masked_secret: c.masked_secret,
      created_at_ms: c.created_at_ms,
      expires_at_ms: c.expires_at_ms,
      is_active: c.is_active,
      trade_enabled: false,
      withdraw_enabled: false,
      read_only: true,
      source: "seed" as const,
    }
  })
  const user: SafeCred[] = listCredentials().map((c) => ({ ...c, source: "user" as const }))
  return [...user, ...seed]
}

export async function credentialRoutes(app: FastifyInstance) {
  // GET /api/credentials — list all credentials (masked)
  app.get<{
    Querystring: { kind?: string; active?: string; adapter_id?: string }
  }>("/api/credentials", { preHandler: requireAuth }, async (request) => {
    let items = allCredentials()
    const q = request.query

    if (q.kind) items = items.filter((c) => c.kind === q.kind!.toLowerCase())
    if (q.adapter_id) items = items.filter((c) => c.adapter_id === q.adapter_id)
    if (q.active !== undefined) {
      const want = q.active === "true"
      items = items.filter((c) => c.is_active === want)
    }

    return { credentials: items, total: items.length }
  })

  // GET /api/credentials/expiring-soon — credentials expiring within 30 days
  app.get<{ Querystring: { horizon_days?: string } }>(
    "/api/credentials/expiring-soon",
    { preHandler: requireAuth },
    async (request) => {
      const horizonDays = parseInt(request.query.horizon_days ?? "30", 10)
      const now = Date.now()
      const horizon = now + horizonDays * 86_400_000
      const expiring = allCredentials()
        .filter(
          (c) => c.expires_at_ms !== null && c.expires_at_ms > now && c.expires_at_ms <= horizon && c.is_active,
        )
        .map((c) => ({
          ref_id: c.ref_id,
          label: c.label,
          adapter_id: c.adapter_id,
          expires_at_ms: c.expires_at_ms,
          days_remaining: Math.ceil(((c.expires_at_ms ?? 0) - now) / 86_400_000),
          trade_enabled: false,
          withdraw_enabled: false,
          read_only: true,
        }))
      return { expiring, total: expiring.length, horizon_days: horizonDays }
    },
  )

  // GET /api/credentials/:ref_id — single credential (masked)
  app.get<{ Params: { ref_id: string } }>(
    "/api/credentials/:ref_id",
    { preHandler: requireAuth },
    async (request, reply) => {
      const cred = allCredentials().find((c) => c.ref_id === request.params.ref_id)
      if (!cred) return reply.code(404).send({ error: "Credential not found" })
      return cred
    },
  )

  // POST /api/credentials — register new credential (secret encrypted, never returned)
  app.post<{
    Body: { kind: string; adapter_id: string; label: string; secret: string; expires_at_ms?: number | null }
  }>(
    "/api/credentials",
    {
      preHandler: requireAuth,
      schema: {
        body: {
          type: "object",
          required: ["kind", "adapter_id", "label", "secret"],
          properties: {
            kind: { type: "string", enum: ["api_key", "hmac_secret", "bearer_token", "oauth2_client"] },
            adapter_id: { type: "string", minLength: 1, maxLength: 64 },
            label: { type: "string", minLength: 1, maxLength: 200 },
            secret: { type: "string", minLength: 8, maxLength: 4096 },
            expires_at_ms: { type: ["integer", "null"] },
          },
        },
      },
    },
    async (request, reply) => {
      try {
        const cred = addCredential({
          kind: request.body.kind,
          adapter_id: request.body.adapter_id,
          label: request.body.label,
          secret: request.body.secret,
          expires_at_ms: request.body.expires_at_ms ?? null,
        })
        // SECURITY: response never contains the secret
        return reply.code(201).send({ ...cred, source: "user" })
      } catch (e) {
        return reply.code(400).send({ error: e instanceof Error ? e.message : "Bad request" })
      }
    },
  )

  // DELETE /api/credentials/:ref_id — soft delete user, or clear seed override
  app.delete<{ Params: { ref_id: string } }>(
    "/api/credentials/:ref_id",
    { preHandler: requireAuth },
    async (request, reply) => {
      const ref_id = request.params.ref_id
      if (ref_id.startsWith("cred-user-")) {
        const ok = deactivateCredential(ref_id)
        if (!ok) return reply.code(404).send({ error: "Credential not found" })
        const updated = getCredential(ref_id)
        return { ok: true, credential: updated }
      }
      // Seed credential — clear override (revert to mock value)
      const cleared = clearSeedOverride(ref_id)
      if (!cleared) {
        return reply.code(404).send({ error: "No override exists for this seed credential" })
      }
      return { ok: true, reverted: true }
    },
  )

  // PUT /api/credentials/:ref_id — edit credential (seed → upserts override; user → not yet supported)
  app.put<{
    Body: { secret: string; label?: string; expires_at_ms?: number | null }
    Params: { ref_id: string }
  }>(
    "/api/credentials/:ref_id",
    {
      preHandler: requireAuth,
      schema: {
        body: {
          type: "object",
          required: ["secret"],
          properties: {
            secret: { type: "string", minLength: 8, maxLength: 4096 },
            label: { type: "string", minLength: 1, maxLength: 200 },
            expires_at_ms: { type: ["integer", "null"] },
          },
        },
      },
    },
    async (request, reply) => {
      const ref_id = request.params.ref_id

      if (ref_id.startsWith("cred-user-")) {
        return reply.code(400).send({
          error: "User-added credentials cannot be edited. Delete and re-add to rotate.",
        })
      }

      // Seed credential — find kind from mock to use right mask prefix
      const seed = CREDENTIALS.find((c) => c.ref_id === ref_id)
      if (!seed) {
        return reply.code(404).send({ error: "Seed credential not found" })
      }

      try {
        const ov = setSeedOverride({
          ref_id,
          kind: seed.kind,
          secret: request.body.secret,
          label: request.body.label,
          expires_at_ms: request.body.expires_at_ms ?? null,
        })
        return { ok: true, ref_id, masked_secret: ov.masked_secret, updated_at_ms: ov.updated_at_ms }
      } catch (e) {
        return reply.code(400).send({ error: e instanceof Error ? e.message : "Bad request" })
      }
    },
  )
}
