import type { FastifyInstance } from "fastify"
import { requireAuth } from "../auth.js"
import { ADAPTERS } from "../mock/data.js"

export async function adapterRoutes(app: FastifyInstance) {
  // GET /api/adapters — list all adapters with optional filters
  app.get<{
    Querystring: { trust_band?: string; source_family?: string; healthy?: string; active?: string }
  }>("/api/adapters", { preHandler: requireAuth }, async (request) => {
    let result = [...ADAPTERS]
    const { trust_band, source_family, healthy, active } = request.query

    if (trust_band) {
      result = result.filter((a) => a.trust_band === trust_band.toUpperCase())
    }
    if (source_family) {
      result = result.filter((a) => a.source_family === source_family.toUpperCase())
    }
    if (healthy !== undefined) {
      const want = healthy === "true"
      result = result.filter((a) => a.is_healthy === want)
    }
    if (active !== undefined) {
      const want = active === "true"
      result = result.filter((a) => a.is_active === want)
    }
    return { adapters: result, total: result.length }
  })

  // GET /api/adapters/:id
  app.get<{ Params: { id: string } }>("/api/adapters/:id", { preHandler: requireAuth }, async (request, reply) => {
    const adapter = ADAPTERS.find((a) => a.adapter_id === request.params.id)
    if (!adapter) return reply.code(404).send({ error: "Adapter not found" })
    return adapter
  })

  // GET /api/adapter-trust — trust band summary
  app.get("/api/adapter-trust", { preHandler: requireAuth }, async () => {
    const bands = ["TRUSTED", "PROVISIONAL", "QUARANTINED", "REVOKED"]
    const summary = bands.map((band) => ({
      trust_band: band,
      count: ADAPTERS.filter((a) => a.trust_band === band).length,
      adapters: ADAPTERS.filter((a) => a.trust_band === band).map((a) => ({
        adapter_id: a.adapter_id,
        name: a.name,
        is_healthy: a.is_healthy,
        is_fresh: a.is_fresh,
      })),
    }))
    return { summary, captured_at_ms: Date.now() }
  })

  // GET /api/source-trust — by source family
  app.get("/api/source-trust", { preHandler: requireAuth }, async () => {
    const families = [...new Set(ADAPTERS.map((a) => a.source_family))]
    const summary = families.map((family) => {
      const adapters = ADAPTERS.filter((a) => a.source_family === family)
      return {
        source_family: family,
        total: adapters.length,
        healthy: adapters.filter((a) => a.is_healthy).length,
        avg_error_rate: adapters.reduce((s, a) => s + (a.error_rate ?? 0), 0) / adapters.length,
        adapters: adapters.map((a) => ({
          adapter_id: a.adapter_id,
          name: a.name,
          trust_band: a.trust_band,
          is_healthy: a.is_healthy,
          error_rate: a.error_rate,
        })),
      }
    })
    return { summary, captured_at_ms: Date.now() }
  })

  // GET /api/health/adapters — adapter health check
  app.get("/api/health/adapters", { preHandler: requireAuth }, async () => {
    return {
      total: ADAPTERS.length,
      healthy: ADAPTERS.filter((a) => a.is_healthy).length,
      stale: ADAPTERS.filter((a) => !a.is_fresh && a.is_active).length,
      quarantined: ADAPTERS.filter((a) => a.trust_band === "QUARANTINED").length,
      revoked: ADAPTERS.filter((a) => a.trust_band === "REVOKED").length,
      degraded: ADAPTERS.filter((a) => a.is_healthy).length < ADAPTERS.filter((a) => a.is_active).length,
      captured_at_ms: Date.now(),
    }
  })
}
