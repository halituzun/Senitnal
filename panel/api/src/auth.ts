// Auth middleware: local dev (email+password) or Cloudflare Access (CF-Access-Authenticated-User-Email)
import type { FastifyRequest, FastifyReply } from "fastify"
import crypto from "node:crypto"

const IS_PROD = process.env["NODE_ENV"] === "production"
const CF_ACCESS_HEADER = "cf-access-authenticated-user-email"

// Local dev credentials — read from env or auto-generated
let _devPassword: string | null = null

function getDevPassword(): string {
  if (_devPassword) return _devPassword
  const fromEnv = process.env["PANEL_AUTH_PASSWORD"]
  if (fromEnv && fromEnv.length >= 8) {
    _devPassword = fromEnv
  } else {
    // Generate a random 12-char password for this process lifetime
    _devPassword = crypto.randomBytes(9).toString("base64").replace(/[^a-zA-Z0-9]/g, "").slice(0, 12)
    console.log("\n╔═══════════════════════════════════════╗")
    console.log("║   PANEL LOCAL DEV CREDENTIALS         ║")
    console.log(`║   Email:    ${(process.env["PANEL_AUTH_EMAIL"] ?? "panel@senitnal.local").padEnd(25)} ║`)
    console.log(`║   Password: ${_devPassword.padEnd(25)} ║`)
    console.log("╚═══════════════════════════════════════╝\n")
  }
  return _devPassword
}

export function getLocalDevCredentials() {
  return {
    email: process.env["PANEL_AUTH_EMAIL"] ?? "panel@senitnal.local",
    password: getDevPassword(),
  }
}

function safeEqual(a: string, b: string): boolean {
  const bufA = Buffer.from(a)
  const bufB = Buffer.from(b)
  if (bufA.length !== bufB.length) {
    // Always compare to prevent timing leaks on length
    crypto.timingSafeEqual(bufA, bufA)
    return false
  }
  return crypto.timingSafeEqual(bufA, bufB)
}

export function verifyLocalCredentials(email: string, password: string): boolean {
  if (IS_PROD) return false
  const creds = getLocalDevCredentials()
  return safeEqual(email, creds.email) && safeEqual(password, creds.password)
}

export async function requireAuth(request: FastifyRequest, reply: FastifyReply) {
  if (IS_PROD) {
    // Cloudflare Access sets this header — required in production
    const cfEmail = request.headers[CF_ACCESS_HEADER]
    if (!cfEmail || typeof cfEmail !== "string") {
      reply.code(403).send({ error: "Forbidden — Cloudflare Access required" })
      return
    }
    // Attach to request for audit logging
    ;(request as FastifyRequest & { userEmail?: string }).userEmail = cfEmail
    return
  }

  // Local dev: check JWT cookie
  const token = request.cookies?.["panel_session"]
  if (!token) {
    reply.code(401).send({ error: "Unauthorized" })
    return
  }

  try {
    const payload = await request.jwtVerify<{ email: string }>()
    ;(request as FastifyRequest & { userEmail?: string }).userEmail = payload.email
  } catch {
    reply.code(401).send({ error: "Invalid or expired session" })
  }
}
