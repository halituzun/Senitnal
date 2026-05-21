import type { FastifyInstance } from "fastify"
import { requireAuth } from "../auth.js"
import { STRATEGIES, PORTFOLIO } from "../mock/data.js"

export async function portfolioRoutes(app: FastifyInstance) {
  // GET /api/portfolio — portfolio configuration and summary
  app.get("/api/portfolio", { preHandler: requireAuth }, async () => {
    return { ...PORTFOLIO, captured_at_ms: Date.now() }
  })

  // GET /api/strategies — list strategies with optional filters
  app.get<{
    Querystring: { lifecycle_state?: string; enabled?: string }
  }>("/api/strategies", { preHandler: requireAuth }, async (request) => {
    let items = [...STRATEGIES]
    const { lifecycle_state, enabled } = request.query

    if (lifecycle_state) {
      items = items.filter((s) => s.lifecycle_state === lifecycle_state.toUpperCase())
    }
    if (enabled !== undefined) {
      const want = enabled === "true"
      items = items.filter((s) => s.enabled === want)
    }

    return { strategies: items, total: items.length }
  })

  // GET /api/strategies/:id
  app.get<{ Params: { id: string } }>("/api/strategies/:id", { preHandler: requireAuth }, async (request, reply) => {
    const item = STRATEGIES.find((s) => s.strategy_id === request.params.id)
    if (!item) return reply.code(404).send({ error: "Strategy not found" })
    return item
  })
}
