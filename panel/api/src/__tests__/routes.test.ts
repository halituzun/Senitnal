// API route integration tests
import { describe, it, expect, beforeAll, afterAll } from "vitest"
import Fastify from "fastify"
import fastifyCookie from "@fastify/cookie"
import fastifyJwt from "@fastify/jwt"
import fastifyCors from "@fastify/cors"

import { authRoutes } from "../routes/auth.js"
import { dashboardRoutes } from "../routes/dashboard.js"
import { adapterRoutes } from "../routes/adapters.js"
import { ledgerRoutes } from "../routes/ledger.js"
import { decisionRoutes } from "../routes/decisions.js"
import { credentialRoutes } from "../routes/credentials.js"
import { miscRoutes } from "../routes/misc.js"

const TEST_EMAIL = "test@senitnal.local"
const TEST_PASSWORD = "TestPass123"

process.env["PANEL_AUTH_EMAIL"] = TEST_EMAIL
process.env["PANEL_AUTH_PASSWORD"] = TEST_PASSWORD

const app = Fastify({ logger: false })

beforeAll(async () => {
  await app.register(fastifyCors, { origin: true, credentials: true })
  await app.register(fastifyCookie)
  await app.register(fastifyJwt, {
    secret: "test-jwt-secret-32-chars-minimum-ok",
    cookie: { cookieName: "panel_session", signed: false },
  })
  await app.register(authRoutes)
  await app.register(dashboardRoutes)
  await app.register(adapterRoutes)
  await app.register(ledgerRoutes)
  await app.register(decisionRoutes)
  await app.register(credentialRoutes)
  await app.register(miscRoutes)
  app.get("/ping", async () => ({ ok: true }))
  await app.ready()
})

afterAll(async () => {
  await app.close()
})

async function getSession(): Promise<string> {
  const res = await app.inject({
    method: "POST",
    url: "/api/auth/login",
    payload: { email: TEST_EMAIL, password: TEST_PASSWORD },
  })
  const cookies = res.cookies
  const session = cookies.find((c) => c.name === "panel_session")
  return session?.value ?? ""
}

describe("Auth", () => {
  it("GET /ping → 200", async () => {
    const res = await app.inject({ method: "GET", url: "/ping" })
    expect(res.statusCode).toBe(200)
    expect(res.json()).toMatchObject({ ok: true })
  })

  it("POST /api/auth/login with valid credentials → 200", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/auth/login",
      payload: { email: TEST_EMAIL, password: TEST_PASSWORD },
    })
    expect(res.statusCode).toBe(200)
    expect(res.json()).toMatchObject({ ok: true, email: TEST_EMAIL })
  })

  it("POST /api/auth/login with wrong password → 401", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/auth/login",
      payload: { email: TEST_EMAIL, password: "wrongpass" },
    })
    expect(res.statusCode).toBe(401)
  })

  it("GET /api/auth/me without session → 401", async () => {
    const res = await app.inject({ method: "GET", url: "/api/auth/me" })
    expect(res.statusCode).toBe(401)
  })
})

describe("Dashboard", () => {
  it("GET /api/dashboard requires auth", async () => {
    const res = await app.inject({ method: "GET", url: "/api/dashboard" })
    expect(res.statusCode).toBe(401)
  })

  it("GET /api/dashboard with session → portfolio data", async () => {
    const token = await getSession()
    const res = await app.inject({
      method: "GET",
      url: "/api/dashboard",
      cookies: { panel_session: token },
    })
    expect(res.statusCode).toBe(200)
    const body = res.json()
    expect(body).toHaveProperty("portfolio")
    expect(body).toHaveProperty("adapter_hub")
    expect(body).toHaveProperty("pnl_summary")
    expect(body.adapter_hub.total_adapters).toBe(23)
  })
})

describe("Adapters", () => {
  it("GET /api/adapters → 23 total", async () => {
    const token = await getSession()
    const res = await app.inject({
      method: "GET",
      url: "/api/adapters",
      cookies: { panel_session: token },
    })
    expect(res.statusCode).toBe(200)
    expect(res.json().total).toBe(23)
  })

  it("GET /api/adapters?trust_band=QUARANTINED → 1 quarantined", async () => {
    const token = await getSession()
    const res = await app.inject({
      method: "GET",
      url: "/api/adapters?trust_band=QUARANTINED",
      cookies: { panel_session: token },
    })
    expect(res.statusCode).toBe(200)
    expect(res.json().total).toBe(1)
    expect(res.json().adapters[0].trust_band).toBe("QUARANTINED")
  })

  it("GET /api/adapters?trust_band=REVOKED → 1 revoked", async () => {
    const token = await getSession()
    const res = await app.inject({
      method: "GET",
      url: "/api/adapters?trust_band=REVOKED",
      cookies: { panel_session: token },
    })
    expect(res.statusCode).toBe(200)
    expect(res.json().total).toBe(1)
  })

  it("GET /api/adapters/:id with valid id → 200", async () => {
    const token = await getSession()
    const res = await app.inject({
      method: "GET",
      url: "/api/adapters/taapi-pro",
      cookies: { panel_session: token },
    })
    expect(res.statusCode).toBe(200)
    expect(res.json().adapter_id).toBe("taapi-pro")
  })

  it("GET /api/adapters/:id with invalid id → 404", async () => {
    const token = await getSession()
    const res = await app.inject({
      method: "GET",
      url: "/api/adapters/does-not-exist",
      cookies: { panel_session: token },
    })
    expect(res.statusCode).toBe(404)
  })
})

describe("Observer Ledger", () => {
  it("GET /api/observer-ledger → 50 total events", async () => {
    const token = await getSession()
    const res = await app.inject({
      method: "GET",
      url: "/api/observer-ledger",
      cookies: { panel_session: token },
    })
    expect(res.statusCode).toBe(200)
    const body = res.json()
    expect(body.total).toBe(50)
    expect(body.items.length).toBeLessThanOrEqual(25)
  })

  it("GET /api/observer-ledger?severity=ERROR → only ERROR events", async () => {
    const token = await getSession()
    const res = await app.inject({
      method: "GET",
      url: "/api/observer-ledger?severity=ERROR",
      cookies: { panel_session: token },
    })
    expect(res.statusCode).toBe(200)
    const items = res.json().items as Array<{ severity: string }>
    expect(items.every((e) => e.severity === "ERROR")).toBe(true)
  })
})

describe("Credentials — security", () => {
  it("credentials never contain full_secret field", async () => {
    const token = await getSession()
    const res = await app.inject({
      method: "GET",
      url: "/api/credentials",
      cookies: { panel_session: token },
    })
    expect(res.statusCode).toBe(200)
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const creds = res.json().credentials as Array<Record<string, any>>
    for (const c of creds) {
      expect(c).not.toHaveProperty("full_secret")
      expect(c["trade_enabled"]).toBe(false)
      expect(c["withdraw_enabled"]).toBe(false)
      expect(c["read_only"]).toBe(true)
    }
  })

  it("credentials have masked_secret field", async () => {
    const token = await getSession()
    const res = await app.inject({
      method: "GET",
      url: "/api/credentials",
      cookies: { panel_session: token },
    })
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const creds = res.json().credentials as Array<Record<string, any>>
    for (const c of creds) {
      expect(typeof c["masked_secret"]).toBe("string")
      expect(String(c["masked_secret"])).toContain("•")
    }
  })

  it("POST /api/credentials encrypts secret, returns only masked", async () => {
    const token = await getSession()
    const TEST_SECRET = "extremely-fake-secret-for-test-purposes-only-xyz"
    const res = await app.inject({
      method: "POST",
      url: "/api/credentials",
      cookies: { panel_session: token },
      payload: {
        kind: "api_key",
        adapter_id: "test-vault-adapter",
        label: "Vault Test",
        secret: TEST_SECRET,
      },
    })
    expect(res.statusCode).toBe(201)
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const body = res.json() as Record<string, any>
    // Response must NOT contain the plaintext secret anywhere
    const bodyStr = JSON.stringify(body)
    expect(bodyStr).not.toContain(TEST_SECRET)
    expect(bodyStr).not.toContain("extremely-fake")
    expect(body["trade_enabled"]).toBe(false)
    expect(body["withdraw_enabled"]).toBe(false)
    expect(body["read_only"]).toBe(true)
    expect(String(body["ref_id"])).toMatch(/^cred-user-/)
    expect(String(body["masked_secret"])).toContain("•")
  })

  it("POST /api/credentials rejects short secret", async () => {
    const token = await getSession()
    const res = await app.inject({
      method: "POST",
      url: "/api/credentials",
      cookies: { panel_session: token },
      payload: { kind: "api_key", adapter_id: "a", label: "x", secret: "short" },
    })
    expect(res.statusCode).toBe(400)
  })

  it("POST /api/credentials rejects invalid kind", async () => {
    const token = await getSession()
    const res = await app.inject({
      method: "POST",
      url: "/api/credentials",
      cookies: { panel_session: token },
      payload: { kind: "trade_key", adapter_id: "a", label: "x", secret: "longenough12345" },
    })
    expect(res.statusCode).toBe(400)
  })

  it("DELETE /api/credentials/:id on seed without override → 404", async () => {
    const token = await getSession()
    const res = await app.inject({
      method: "DELETE",
      url: "/api/credentials/cred-cryptopanic",
      cookies: { panel_session: token },
    })
    expect(res.statusCode).toBe(404)
  })

  it("PUT /api/credentials/:id on seed → upserts override, masked fingerprint changes", async () => {
    const token = await getSession()
    const TEST_SECRET = "rotation-secret-fake-1234567890"

    // Get original
    const before = await app.inject({
      method: "GET",
      url: "/api/credentials/cred-taapi-prod",
      cookies: { panel_session: token },
    })
    const originalMask = (before.json() as { masked_secret: string }).masked_secret

    // Override
    const put = await app.inject({
      method: "PUT",
      url: "/api/credentials/cred-taapi-prod",
      cookies: { panel_session: token },
      payload: { secret: TEST_SECRET, label: "TAAPI rotated" },
    })
    expect(put.statusCode).toBe(200)
    const putBody = put.json() as { ok: boolean; masked_secret: string }
    expect(putBody.ok).toBe(true)
    expect(putBody.masked_secret).not.toBe(originalMask)
    // Response must not contain plaintext
    expect(JSON.stringify(put.json())).not.toContain(TEST_SECRET)

    // GET shows overridden
    const after = await app.inject({
      method: "GET",
      url: "/api/credentials/cred-taapi-prod",
      cookies: { panel_session: token },
    })
    const afterBody = after.json() as { overridden: boolean; masked_secret: string; label: string }
    expect(afterBody.overridden).toBe(true)
    expect(afterBody.masked_secret).toBe(putBody.masked_secret)
    expect(afterBody.label).toBe("TAAPI rotated")

    // Revert
    const del = await app.inject({
      method: "DELETE",
      url: "/api/credentials/cred-taapi-prod",
      cookies: { panel_session: token },
    })
    expect(del.statusCode).toBe(200)
    expect((del.json() as { reverted: boolean }).reverted).toBe(true)
  })

  it("PUT /api/credentials/:id on user cred → rejects (use add/delete to rotate)", async () => {
    const token = await getSession()
    const res = await app.inject({
      method: "PUT",
      url: "/api/credentials/cred-user-fake",
      cookies: { panel_session: token },
      payload: { secret: "longenoughsecret123" },
    })
    expect(res.statusCode).toBe(400)
  })

  it("DELETE /api/credentials/:id on user cred → soft-deletes", async () => {
    const token = await getSession()
    // First add one
    const create = await app.inject({
      method: "POST",
      url: "/api/credentials",
      cookies: { panel_session: token },
      payload: { kind: "api_key", adapter_id: "x", label: "to-delete", secret: "deletetest12345678" },
    })
    const refId = create.json().ref_id as string

    const del = await app.inject({
      method: "DELETE",
      url: `/api/credentials/${refId}`,
      cookies: { panel_session: token },
    })
    expect(del.statusCode).toBe(200)
    expect(del.json().credential.is_active).toBe(false)
  })
})

describe("Adapters — write", () => {
  it("POST /api/adapters creates new adapter", async () => {
    const token = await getSession()
    const adapterId = `test-adp-${Date.now()}`
    const res = await app.inject({
      method: "POST",
      url: "/api/adapters",
      cookies: { panel_session: token },
      payload: {
        adapter_id: adapterId,
        name: "Test Adapter",
        source_family: "RESEARCH",
      },
    })
    expect(res.statusCode).toBe(201)
    expect(res.json().adapter_id).toBe(adapterId)
    expect(res.json().is_user_added).toBe(true)
  })

  it("POST /api/adapters rejects bad adapter_id format", async () => {
    const token = await getSession()
    const res = await app.inject({
      method: "POST",
      url: "/api/adapters",
      cookies: { panel_session: token },
      payload: {
        adapter_id: "BAD ID WITH SPACES",
        name: "Test",
        source_family: "RESEARCH",
      },
    })
    expect(res.statusCode).toBe(400)
  })

  it("POST /api/adapters rejects invalid source_family", async () => {
    const token = await getSession()
    const res = await app.inject({
      method: "POST",
      url: "/api/adapters",
      cookies: { panel_session: token },
      payload: {
        adapter_id: "test-bad-family",
        name: "Test",
        source_family: "MADE_UP_FAMILY",
      },
    })
    expect(res.statusCode).toBe(400)
  })
})

describe("Forbidden routes — no trade/execute/order", () => {
  it("GET /api/trade → 404", async () => {
    const res = await app.inject({ method: "GET", url: "/api/trade" })
    expect(res.statusCode).toBe(404)
  })

  it("POST /api/trade → 404", async () => {
    const res = await app.inject({ method: "POST", url: "/api/trade", payload: {} })
    expect(res.statusCode).toBe(404)
  })

  it("GET /api/execute → 404", async () => {
    const res = await app.inject({ method: "GET", url: "/api/execute" })
    expect(res.statusCode).toBe(404)
  })

  it("POST /api/order-submit → 404", async () => {
    const res = await app.inject({ method: "POST", url: "/api/order-submit", payload: {} })
    expect(res.statusCode).toBe(404)
  })

  it("POST /api/approve-live → 404", async () => {
    const res = await app.inject({ method: "POST", url: "/api/approve-live", payload: {} })
    expect(res.statusCode).toBe(404)
  })

  it("POST /api/kill-switch/clear → 404", async () => {
    const res = await app.inject({ method: "POST", url: "/api/kill-switch/clear", payload: {} })
    expect(res.statusCode).toBe(404)
  })
})

describe("Health and Policy", () => {
  it("GET /api/health → system status", async () => {
    const token = await getSession()
    const res = await app.inject({
      method: "GET",
      url: "/api/health",
      cookies: { panel_session: token },
    })
    expect(res.statusCode).toBe(200)
    expect(res.json().status).toBe("OK")
  })

  it("GET /api/policy → rules present", async () => {
    const token = await getSession()
    const res = await app.inject({
      method: "GET",
      url: "/api/policy",
      cookies: { panel_session: token },
    })
    expect(res.statusCode).toBe(200)
    expect(res.json().rules.length).toBeGreaterThan(0)
    expect(res.json().kill_switch_active).toBe(false)
  })
})
