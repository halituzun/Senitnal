// Credential routes — NEVER returns full secrets, only masked_secret
import type { FastifyInstance } from "fastify"
import { requireAuth } from "../auth.js"
import { CREDENTIALS } from "../mock/data.js"

export async function credentialRoutes(app: FastifyInstance) {
  // GET /api/credentials — list all credentials (masked)
  app.get<{
    Querystring: { kind?: string; active?: string; adapter_id?: string }
  }>("/api/credentials", { preHandler: requireAuth }, async (request) => {
    let items = [...CREDENTIALS]
    const q = request.query

    if (q.kind) items = items.filter((c) => c.kind === q.kind.toLowerCase())
    if (q.adapter_id) items = items.filter((c) => c.adapter_id === q.adapter_id)
    if (q.active !== undefined) {
      const want = q.active === "true"
      items = items.filter((c) => c.is_active === want)
    }

    // SECURITY: strip any hypothetical full_secret field — only masked_secret passes through
    const safe = items.map(({ masked_secret, ...rest }) => ({
      ...rest,
      masked_secret,
      trade_enabled: false,
      withdraw_enabled: false,
      read_only: true,
    }))

    return { credentials: safe, total: safe.length }
  })

  // GET /api/credentials/:ref_id — single credential (masked)
  app.get<{ Params: { ref_id: string } }>(
    "/api/credentials/:ref_id",
    { preHandler: requireAuth },
    async (request, reply) => {
      const cred = CREDENTIALS.find((c) => c.ref_id === request.params.ref_id)
      if (!cred) return reply.code(404).send({ error: "Credential not found" })
      const { masked_secret, ...rest } = cred
      return {
        ...rest,
        masked_secret,
        trade_enabled: false,
        withdraw_enabled: false,
        read_only: true,
      }
    },
  )

  // GET /api/credentials/expiring-soon — credentials expiring within 30 days
  app.get<{ Querystring: { horizon_days?: string } }>(
    "/api/credentials/expiring-soon",
    { preHandler: requireAuth },
    async (request) => {
      const horizonDays = parseInt(request.query.horizon_days ?? "30", 10)
      const now = Date.now()
      const horizon = now + horizonDays * 86_400_000
      const expiring = CREDENTIALS.filter(
        (c) => c.expires_at_ms !== null && c.expires_at_ms > now && c.expires_at_ms <= horizon && c.is_active,
      ).map((c) => ({
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
}
