import type { FastifyInstance } from "fastify"
import { requireAuth } from "../auth.js"
import { MEMORY_RECORDS } from "../mock/data.js"

export async function memoryRoutes(app: FastifyInstance) {
  // GET /api/memory-recall — paginated + filtered memory
  app.get<{
    Querystring: {
      page?: string
      per_page?: string
      strategy_id?: string
      pattern_type?: string
      min_confidence?: string
    }
  }>("/api/memory-recall", { preHandler: requireAuth }, async (request) => {
    let items = [...MEMORY_RECORDS].sort((a, b) => b.confidence - a.confidence)
    const q = request.query

    if (q.strategy_id) items = items.filter((m) => m.strategy_id === q.strategy_id)
    if (q.pattern_type) items = items.filter((m) => m.pattern_type === q.pattern_type.toUpperCase())
    if (q.min_confidence) items = items.filter((m) => m.confidence >= Number(q.min_confidence))

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

  // GET /api/memory-recall/:id
  app.get<{ Params: { id: string } }>(
    "/api/memory-recall/:id",
    { preHandler: requireAuth },
    async (request, reply) => {
      const item = MEMORY_RECORDS.find((m) => m.memory_id === request.params.id)
      if (!item) return reply.code(404).send({ error: "Memory record not found" })
      return item
    },
  )

  // GET /api/memory-recall/pattern-types — unique pattern types for filter UI
  app.get("/api/memory-recall/pattern-types", { preHandler: requireAuth }, async () => {
    const types = [...new Set(MEMORY_RECORDS.map((m) => m.pattern_type))].sort()
    return { pattern_types: types }
  })
}
