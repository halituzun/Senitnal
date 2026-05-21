import type { FastifyInstance } from "fastify"
import { verifyLocalCredentials, getLocalDevCredentials } from "../auth.js"

export async function authRoutes(app: FastifyInstance) {
  // POST /api/auth/login — local dev only
  app.post<{ Body: { email: string; password: string } }>(
    "/api/auth/login",
    {
      schema: {
        body: {
          type: "object",
          required: ["email", "password"],
          properties: {
            email: { type: "string", format: "email" },
            password: { type: "string", minLength: 1 },
          },
        },
      },
    },
    async (request, reply) => {
      if (process.env["NODE_ENV"] === "production") {
        return reply.code(403).send({ error: "Local login disabled in production — use Cloudflare Access" })
      }

      const { email, password } = request.body
      if (!verifyLocalCredentials(email, password)) {
        return reply.code(401).send({ error: "Invalid credentials" })
      }

      const token = await reply.jwtSign({ email }, { expiresIn: "8h" })
      return reply
        .setCookie("panel_session", token, {
          httpOnly: true,
          secure: false,
          sameSite: "lax",
          path: "/",
          maxAge: 8 * 3600,
        })
        .send({ ok: true, email })
    },
  )

  // POST /api/auth/logout
  app.post("/api/auth/logout", async (_request, reply) => {
    return reply
      .clearCookie("panel_session", { path: "/" })
      .send({ ok: true })
  })

  // GET /api/auth/me
  app.get("/api/auth/me", async (request, reply) => {
    const IS_PROD = process.env["NODE_ENV"] === "production"
    if (IS_PROD) {
      const email = request.headers["cf-access-authenticated-user-email"]
      if (!email || typeof email !== "string") {
        return reply.code(403).send({ error: "Cloudflare Access required" })
      }
      return { email, auth_method: "cloudflare_access" }
    }

    const token = request.cookies?.["panel_session"]
    if (!token) return reply.code(401).send({ error: "Not authenticated" })
    try {
      const payload = await request.jwtVerify<{ email: string }>()
      return { email: payload.email, auth_method: "local_dev" }
    } catch {
      return reply.code(401).send({ error: "Invalid session" })
    }
  })

  // GET /api/auth/dev-credentials — local dev only, shows credentials once
  app.get("/api/auth/dev-credentials", async (_request, reply) => {
    if (process.env["NODE_ENV"] === "production") {
      return reply.code(403).send({ error: "Forbidden in production" })
    }
    const creds = getLocalDevCredentials()
    return { email: creds.email, password: creds.password, note: "Local dev only — never shown in production" }
  })
}
