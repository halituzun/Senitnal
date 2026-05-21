import { createRouter, createWebHistory } from "vue-router"
import { useAuthStore } from "@/stores/auth.js"

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", name: "login", component: () => import("@/pages/LoginPage.vue"), meta: { public: true } },
    { path: "/forbidden", name: "forbidden", component: () => import("@/pages/ForbiddenPage.vue"), meta: { public: true } },
    { path: "/", redirect: "/dashboard" },
    { path: "/dashboard", name: "dashboard", component: () => import("@/pages/DashboardPage.vue") },
    { path: "/evidence", name: "evidence", component: () => import("@/pages/EvidencePage.vue") },
    { path: "/observer-ledger", name: "observer-ledger", component: () => import("@/pages/ObserverLedgerPage.vue") },
    { path: "/decisions", name: "decisions", component: () => import("@/pages/DecisionsPage.vue") },
    { path: "/memory-recall", name: "memory-recall", component: () => import("@/pages/MemoryRecallPage.vue") },
    { path: "/replay", name: "replay", component: () => import("@/pages/ReplayPage.vue") },
    { path: "/policy", name: "policy", component: () => import("@/pages/PolicyPage.vue") },
    { path: "/health", name: "health", component: () => import("@/pages/HealthPage.vue") },
    { path: "/sources", name: "sources", component: () => import("@/pages/SourcesPage.vue") },
    { path: "/source-trust", name: "source-trust", component: () => import("@/pages/SourceTrustPage.vue") },
    { path: "/adapter-trust", name: "adapter-trust", component: () => import("@/pages/AdapterTrustPage.vue") },
    { path: "/exchanges", name: "exchanges", component: () => import("@/pages/ExchangesPage.vue") },
    { path: "/adapters", name: "adapters", component: () => import("@/pages/AdaptersPage.vue") },
    { path: "/adapters/new", name: "adapters-new", component: () => import("@/pages/AdaptersNewPage.vue") },
    { path: "/credentials", name: "credentials", component: () => import("@/pages/CredentialsPage.vue") },
    { path: "/credentials/new", name: "credentials-new", component: () => import("@/pages/CredentialsNewPage.vue") },
    { path: "/credentials/:ref_id/edit", name: "credentials-edit", component: () => import("@/pages/CredentialsEditPage.vue") },
    { path: "/ingress-preview", name: "ingress-preview", component: () => import("@/pages/IngressPreviewPage.vue") },
    { path: "/audit-trail", name: "audit-trail", component: () => import("@/pages/AuditTrailPage.vue") },
    { path: "/ideas", name: "ideas", component: () => import("@/pages/IdeasPage.vue") },
  ],
})

router.beforeEach(async (to) => {
  if (to.meta["public"]) return true
  const auth = useAuthStore()
  if (!auth.checked) await auth.fetchMe()
  if (!auth.isAuthenticated) return { name: "login", query: { redirect: to.fullPath } }
  return true
})

export { router }
