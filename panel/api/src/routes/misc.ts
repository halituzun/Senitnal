// Evidence, Replay, Policy, Health, Sources, Exchanges, Ingress Preview, Audit Trail, Ideas
import type { FastifyInstance } from "fastify"
import { requireAuth } from "../auth.js"
import { ADAPTERS, EXCHANGES, LEDGER_EVENTS, STRATEGIES, PORTFOLIO } from "../mock/data.js"

const IDEAS = [
  {
    idea_id: "idea-001",
    created_at_ms: Date.now() - 7 * 86_400_000,
    title: "Add Crypto Fear & Greed weighted overlay to momentum strategies",
    description: "Use F&G index as a multiplier on confidence score — reduce position size when greed > 80",
    status: "UNDER_REVIEW",
    priority: "HIGH",
    tags: ["sentiment", "risk", "momentum"],
  },
  {
    idea_id: "idea-002",
    created_at_ms: Date.now() - 14 * 86_400_000,
    title: "Integrate CoinGecko developer activity metrics",
    description: "GitHub commit frequency as a long-term signal for fundamentals scoring",
    status: "BACKLOG",
    priority: "LOW",
    tags: ["fundamentals", "onchain", "research"],
  },
  {
    idea_id: "idea-003",
    created_at_ms: Date.now() - 3 * 86_400_000,
    title: "Cross-strategy correlation brake — auto-pause correlated pairs",
    description: "When two strategies signal in same direction with correlation > 0.8, reduce one to preserve diversification",
    status: "IN_PROGRESS",
    priority: "HIGH",
    tags: ["risk", "portfolio", "correlation"],
  },
  {
    idea_id: "idea-004",
    created_at_ms: Date.now() - 21 * 86_400_000,
    title: "Whale Alert integration for large transfer clustering",
    description: "Cluster whale transfers by exchange-destination to improve on-chain accumulation signal quality",
    status: "BACKLOG",
    priority: "MEDIUM",
    tags: ["onchain", "whale", "signal-quality"],
  },
  {
    idea_id: "idea-005",
    created_at_ms: Date.now() - 1 * 86_400_000,
    title: "Replay harness: walk-forward validation across 90-day windows",
    description: "Run replay simulation with 30/60/90-day windows to validate strategy edge consistency",
    status: "UNDER_REVIEW",
    priority: "HIGH",
    tags: ["replay", "validation", "backtesting"],
  },
]

const POLICY_RULES = [
  {
    rule_id: "pol-001",
    name: "Max Daily Loss Gate",
    description: "Halt all strategies when total daily loss exceeds configured limit",
    threshold_try: 500.0,
    current_value_try: 38.2,
    status: "OK",
    active: true,
  },
  {
    rule_id: "pol-002",
    name: "Kill Switch",
    description: "Emergency halt — disables all strategy execution",
    status: "INACTIVE",
    active: false,
  },
  {
    rule_id: "pol-003",
    name: "Max Single Strategy Exposure",
    description: "No single strategy may exceed 50% of total capital",
    threshold_pct: 0.5,
    current_max_pct: 0.35,
    status: "OK",
    active: true,
  },
  {
    rule_id: "pol-004",
    name: "Max Single Exchange Exposure",
    description: "No single exchange may receive more than 70% of routed signals",
    threshold_pct: 0.7,
    current_max_pct: 0.45,
    status: "OK",
    active: true,
  },
  {
    rule_id: "pol-005",
    name: "Max Open Orders Gate",
    description: "Reject new signals when open order count reaches limit",
    threshold: 5,
    current: 2,
    status: "OK",
    active: true,
  },
  {
    rule_id: "pol-006",
    name: "Quarantined Adapter Signal Block",
    description: "Discard all signals from QUARANTINED adapters",
    status: "ACTIVE",
    active: true,
    blocked_adapter_ids: ["rogue-alpha-feed"],
  },
]

export async function miscRoutes(app: FastifyInstance) {
  // GET /api/evidence — evidence bundles (derived from decisions)
  app.get<{
    Querystring: { strategy_id?: string; page?: string; per_page?: string }
  }>("/api/evidence", { preHandler: requireAuth }, async (request) => {
    const now = Date.now()
    let items = LEDGER_EVENTS.filter((e) => e.event_type === "EVIDENCE_STORED")
    if (request.query.strategy_id) {
      items = items.filter((e) => e.strategy_id === request.query.strategy_id)
    }
    const total = items.length
    const page = Math.max(1, parseInt(request.query.page ?? "1", 10))
    const perPage = parseInt(request.query.per_page ?? "25", 10)
    return {
      items: items.slice((page - 1) * perPage, page * perPage),
      total,
      page,
      per_page: perPage,
      total_pages: Math.ceil(total / perPage),
      captured_at_ms: now,
    }
  })

  // GET /api/replay — replay simulation results
  app.get<{
    Querystring: { strategy_id?: string }
  }>("/api/replay", { preHandler: requireAuth }, async (request) => {
    const replayItems = LEDGER_EVENTS.filter(
      (e) => e.event_type === "REPLAY_TRIGGERED" || e.event_type === "REPLAY_COMPLETED",
    )
    let filtered = replayItems
    if (request.query.strategy_id) {
      filtered = filtered.filter((e) => e.strategy_id === request.query.strategy_id)
    }
    return {
      replays: filtered,
      total: filtered.length,
      captured_at_ms: Date.now(),
    }
  })

  // GET /api/policy — policy rules and current status
  app.get("/api/policy", { preHandler: requireAuth }, async () => {
    return {
      rules: POLICY_RULES,
      portfolio_id: PORTFOLIO.portfolio_id,
      kill_switch_active: PORTFOLIO.kill_switch_active,
      captured_at_ms: Date.now(),
    }
  })

  // GET /api/health — system health overview
  app.get("/api/health", { preHandler: requireAuth }, async () => {
    const healthy = ADAPTERS.filter((a) => a.is_healthy).length
    return {
      status: "OK",
      services: {
        api: { status: "OK", latency_ms: 12 },
        db: { status: "OK", latency_ms: 3 },
        redis: { status: "OK", latency_ms: 1 },
      },
      adapters: {
        total: ADAPTERS.length,
        healthy,
        degraded: healthy < ADAPTERS.filter((a) => a.is_active).length,
      },
      portfolio: {
        active_strategies: STRATEGIES.filter((s) => s.lifecycle_state === "ACTIVE_LIVE").length,
        paused_strategies: STRATEGIES.filter((s) => s.lifecycle_state === "PAUSED").length,
        rollback_required: STRATEGIES.filter((s) => s.lifecycle_state === "ROLLBACK_REQUIRED").length,
      },
      captured_at_ms: Date.now(),
    }
  })

  // GET /api/sources — intelligence source families
  app.get("/api/sources", { preHandler: requireAuth }, async () => {
    const families = [...new Set(ADAPTERS.map((a) => a.source_family))]
    const sources = families.map((family) => {
      const adapters = ADAPTERS.filter((a) => a.source_family === family)
      return {
        source_family: family,
        adapter_count: adapters.length,
        active_count: adapters.filter((a) => a.is_active).length,
        healthy_count: adapters.filter((a) => a.is_healthy).length,
        avg_error_rate: adapters.reduce((s, a) => s + (a.error_rate ?? 0), 0) / adapters.length,
      }
    })
    return { sources, captured_at_ms: Date.now() }
  })

  // GET /api/exchanges — exchange connection status
  app.get<{
    Querystring: { status?: string; trade_enabled?: string }
  }>("/api/exchanges", { preHandler: requireAuth }, async (request) => {
    let items = [...EXCHANGES]
    if (request.query.status) {
      items = items.filter((e) => e.status === request.query.status!.toUpperCase())
    }
    // trade_enabled is always false — filter is informational only
    return { exchanges: items, total: items.length, captured_at_ms: Date.now() }
  })

  // GET /api/ingress-preview — latest ingress compilation snapshot
  app.get("/api/ingress-preview", { preHandler: requireAuth }, async () => {
    const recentIngress = LEDGER_EVENTS.filter((e) => e.event_type === "INGRESS_COMPILED").sort(
      (a, b) => b.ts_ms - a.ts_ms,
    )
    return {
      latest_compilation: recentIngress[0] ?? null,
      recent_compilations: recentIngress.slice(0, 5),
      adapter_summary: {
        total: ADAPTERS.length,
        active: ADAPTERS.filter((a) => a.is_active).length,
        healthy: ADAPTERS.filter((a) => a.is_healthy).length,
        stale: ADAPTERS.filter((a) => !a.is_fresh && a.is_active).length,
      },
      captured_at_ms: Date.now(),
    }
  })

  // GET /api/audit-trail — audit log entries
  app.get<{
    Querystring: {
      page?: string
      per_page?: string
      severity?: string
      since_ms?: string
    }
  }>("/api/audit-trail", { preHandler: requireAuth }, async (request) => {
    const q = request.query
    let items = [...LEDGER_EVENTS]
      .filter((e) => ["ERROR", "WARN"].includes(e.severity) || e.event_type.includes("AUDIT"))
      .sort((a, b) => b.ts_ms - a.ts_ms)

    if (q.severity) items = items.filter((e) => e.severity === q.severity!.toUpperCase())
    if (q.since_ms) items = items.filter((e) => e.ts_ms >= Number(q.since_ms))

    const total = items.length
    const page = Math.max(1, parseInt(q.page ?? "1", 10))
    const perPage = Math.min(100, parseInt(q.per_page ?? "25", 10))

    return {
      items: items.slice((page - 1) * perPage, page * perPage),
      total,
      page,
      per_page: perPage,
      total_pages: Math.ceil(total / perPage),
    }
  })

  // GET /api/ideas — improvement ideas backlog
  app.get<{
    Querystring: { status?: string; priority?: string }
  }>("/api/ideas", { preHandler: requireAuth }, async (request) => {
    let items = [...IDEAS]
    if (request.query.status) {
      items = items.filter((i) => i.status === request.query.status!.toUpperCase())
    }
    if (request.query.priority) {
      items = items.filter((i) => i.priority === request.query.priority!.toUpperCase())
    }
    return { ideas: items, total: items.length }
  })
}
