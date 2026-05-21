import type { FastifyInstance } from "fastify"
import { requireAuth } from "../auth.js"
import { LEDGER_EVENTS } from "../mock/data.js"

export async function ledgerRoutes(app: FastifyInstance) {
  // GET /api/observer-ledger — paginated + filtered ledger events
  app.get<{
    Querystring: {
      page?: string
      per_page?: string
      severity?: string
      event_type?: string
      strategy_id?: string
      adapter_id?: string
      source?: string
      since_ms?: string
      until_ms?: string
    }
  }>("/api/observer-ledger", { preHandler: requireAuth }, async (request) => {
    let events = [...LEDGER_EVENTS].sort((a, b) => b.ts_ms - a.ts_ms)
    const q = request.query

    if (q.severity) events = events.filter((e) => e.severity === q.severity.toUpperCase())
    if (q.event_type) events = events.filter((e) => e.event_type === q.event_type.toUpperCase())
    if (q.strategy_id) events = events.filter((e) => e.strategy_id === q.strategy_id)
    if (q.adapter_id) events = events.filter((e) => e.adapter_id === q.adapter_id)
    if (q.source) events = events.filter((e) => e.source === q.source)
    if (q.since_ms) events = events.filter((e) => e.ts_ms >= Number(q.since_ms))
    if (q.until_ms) events = events.filter((e) => e.ts_ms <= Number(q.until_ms))

    const total = events.length
    const page = Math.max(1, parseInt(q.page ?? "1", 10))
    const perPage = Math.min(100, parseInt(q.per_page ?? "25", 10))
    const offset = (page - 1) * perPage
    const items = events.slice(offset, offset + perPage)

    return {
      items,
      total,
      page,
      per_page: perPage,
      total_pages: Math.ceil(total / perPage),
    }
  })

  // GET /api/observer-ledger/event-types — unique event types for filter UI
  app.get("/api/observer-ledger/event-types", { preHandler: requireAuth }, async () => {
    const types = [...new Set(LEDGER_EVENTS.map((e) => e.event_type))].sort()
    return { event_types: types }
  })

  // GET /api/observer-ledger/sources — unique sources for filter UI
  app.get("/api/observer-ledger/sources", { preHandler: requireAuth }, async () => {
    const sources = [...new Set(LEDGER_EVENTS.map((e) => e.source))].sort()
    return { sources }
  })
}
