import { describe, it, expect, vi, beforeEach } from "vitest"
import { mount } from "@vue/test-utils"
import { createPinia, setActivePinia } from "pinia"
import { createRouter, createWebHistory } from "vue-router"
import { ref } from "vue"
import DashboardPage from "../pages/DashboardPage.vue"

const mockDashboard = {
  portfolio: {
    approved_capital_value: 10000,
    total_allocated_try: 7500,
    active_strategy_count: 3,
    paused_strategy_count: 1,
    kill_switch_active: false,
  },
  pnl_summary: {
    today_try: 127.3,
    week_try: 681,
    month_try: 2145,
  },
  adapter_hub: {
    total_adapters: 15,
    healthy_count: 12,
    stale_count: 1,
    quarantined_count: 2,
    revoked_count: 1,
    degraded: false,
  },
  recent_events: [
    { id: "ev-1", ts_ms: Date.now() - 120000, severity: "INFO", event_type: "SIGNAL_RECEIVED", message: "RSI=68.4 on BTC/USDT" },
    { id: "ev-2", ts_ms: Date.now() - 300000, severity: "WARN", event_type: "ADAPTER_STALE", message: "Fear & Greed stale for 8h" },
  ],
  captured_at_ms: Date.now(),
}

let mockData = ref(null) as ReturnType<typeof ref>
let mockLoading = ref(false)
let mockError = ref<string | null>(null)

vi.mock("../composables/useFetch", () => ({
  useFetch: () => ({
    data: mockData,
    loading: mockLoading,
    error: mockError,
    execute: vi.fn(),
  }),
}))

function createStubRouter() {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: "/", redirect: "/dashboard" },
      { path: "/dashboard", name: "dashboard", component: DashboardPage },
      { path: "/login", name: "login", component: { template: "<div>Login</div>" }, meta: { public: true } },
    ],
  })
}

describe("DashboardPage", () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    mockData = ref(null)
    mockLoading = ref(false)
    mockError = ref(null)
  })

  it("renders loading state", () => {
    mockLoading.value = true
    const wrapper = mount(DashboardPage, {
      global: { plugins: [createStubRouter()] },
    })
    expect(wrapper.text()).toContain("Loading")
  })

  it("renders portfolio stats with data", () => {
    mockData.value = mockDashboard
    const wrapper = mount(DashboardPage, {
      global: { plugins: [createStubRouter()] },
    })

    expect(wrapper.text()).toContain("10.000")
    expect(wrapper.text()).toContain("7.500")
    expect(wrapper.text()).toContain("75.0%")
    expect(wrapper.text()).toContain("OFF")
    expect(wrapper.text()).toContain("+127,3")
    expect(wrapper.text()).toContain("RSI=68.4")
  })

  it("shows error state", () => {
    mockError.value = "Network failure"
    const wrapper = mount(DashboardPage, {
      global: { plugins: [createStubRouter()] },
    })
    expect(wrapper.text()).toContain("Network failure")
  })
})
