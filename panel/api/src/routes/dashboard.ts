import type { FastifyInstance } from "fastify"
import { requireAuth } from "../auth.js"
import { DASHBOARD } from "../mock/data.js"

export async function dashboardRoutes(app: FastifyInstance) {
  app.get("/api/dashboard", { preHandler: requireAuth }, async () => {
    return { ...DASHBOARD, captured_at_ms: Date.now() }
  })
}
