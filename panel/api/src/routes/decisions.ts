import type { FastifyInstance } from "fastify"
import { requireAuth } from "../auth.js"
import { DECISIONS } from "../mock/data.js"

export async function decisionRoutes(app: FastifyInstance) {
  // GET /api/decisions — paginated + filtered decisions
  app.get<{
    Querystring: {
      page?: string
      per_page?: string
      outcome?: string
      strategy_id?: string
      gate_name?: string
    }
  }>("/api/decisions", { preHandler: requireAuth }, async (request) => {
    let items = [...DECISIONS].sort((a, b) => b.ts_ms - a.ts_ms)
    const q = request.query

    if (q.outcome) items = items.filter((d) => d.outcome === q.outcome.toUpperCase())
    if (q.strategy_id) items = items.filter((d) => d.strategy_id === q.strategy_id)
    if (q.gate_name) items = items.filter((d) => d.gate_name === q.gate_name)

    const total = items.length
    const page = Math.max(1, parseInt(q.page ?? "1", 10))
    const perPage = Math.min(100, parseInt(q.per_page ?? "25", 10))
    const offset = (page - 1) * perPage

    return {
      items: items.slice(offset, offset + perPage),
      total,
      page,
      per_page: perPage,
      total_pages: Math.ceil(total / perPage),
    }
  })

  // GET /api/decisions/:id
  app.get<{ Params: { id: string } }>("/api/decisions/:id", { preHandler: requireAuth }, async (request, reply) => {
    const item = DECISIONS.find((d) => d.decision_id === request.params.id)
    if (!item) return reply.code(404).send({ error: "Decision not found" })
    return item
  })
}
