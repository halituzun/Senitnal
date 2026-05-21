import Fastify from "fastify"
import fastifyCookie from "@fastify/cookie"
import fastifyJwt from "@fastify/jwt"
import fastifyCors from "@fastify/cors"
import fastifyRateLimit from "@fastify/rate-limit"

import { authRoutes } from "./routes/auth.js"
import { dashboardRoutes } from "./routes/dashboard.js"
import { adapterRoutes } from "./routes/adapters.js"
import { ledgerRoutes } from "./routes/ledger.js"
import { decisionRoutes } from "./routes/decisions.js"
import { memoryRoutes } from "./routes/memory.js"
import { credentialRoutes } from "./routes/credentials.js"
import { portfolioRoutes } from "./routes/portfolio.js"
import { miscRoutes } from "./routes/misc.js"
import { getLocalDevCredentials } from "./auth.js"

const IS_PROD = process.env["NODE_ENV"] === "production"
const PORT = parseInt(process.env["PANEL_API_PORT"] ?? "3787", 10)
const HOST = process.env["PANEL_API_HOST"] ?? "0.0.0.0"
const JWT_SECRET = process.env["PANEL_JWT_SECRET"] ?? "dev-jwt-secret-change-in-production-min-32-chars"

if (IS_PROD && JWT_SECRET === "dev-jwt-secret-change-in-production-min-32-chars") {
  console.error("FATAL: PANEL_JWT_SECRET must be set in production")
  process.exit(1)
}

const app = Fastify({
  logger: {
    level: IS_PROD ? "warn" : "info",
  },
})

// Plugins
await app.register(fastifyCors, {
  origin: IS_PROD ? false : ["http://localhost:5173", "http://localhost:8787"],
  credentials: true,
})

await app.register(fastifyCookie)

await app.register(fastifyJwt, {
  secret: JWT_SECRET,
  cookie: { cookieName: "panel_session", signed: false },
})

await app.register(fastifyRateLimit, {
  max: 200,
  timeWindow: "1 minute",
})

// Routes
await app.register(authRoutes)
await app.register(dashboardRoutes)
await app.register(adapterRoutes)
await app.register(ledgerRoutes)
await app.register(decisionRoutes)
await app.register(memoryRoutes)
await app.register(credentialRoutes)
await app.register(portfolioRoutes)
await app.register(miscRoutes)

// Health ping (no auth)
app.get("/ping", async () => ({ ok: true, ts: Date.now() }))

// 404 handler
app.setNotFoundHandler((_request, reply) => {
  reply.code(404).send({ error: "Not found" })
})

try {
  await app.listen({ port: PORT, host: HOST })
  if (!IS_PROD) {
    const creds = getLocalDevCredentials()
    console.log(`\nPanel API running at http://localhost:${PORT}`)
    console.log(`Login: ${creds.email} / ${creds.password}`)
  }
} catch (err) {
  app.log.error(err)
  process.exit(1)
}
