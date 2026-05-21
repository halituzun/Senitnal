import { defineStore } from "pinia"
import { ref } from "vue"

export const useAuthStore = defineStore("auth", () => {
  const email = ref<string | null>(null)
  const authMethod = ref<string | null>(null)
  const checked = ref(false)

  const isAuthenticated = ref(false)

  async function fetchMe() {
    try {
      const res = await fetch("/api/auth/me", { credentials: "include" })
      if (res.ok) {
        const data = (await res.json()) as { email: string; auth_method: string }
        email.value = data.email
        authMethod.value = data.auth_method
        isAuthenticated.value = true
      } else {
        isAuthenticated.value = false
      }
    } catch {
      isAuthenticated.value = false
    } finally {
      checked.value = true
    }
  }

  async function login(emailInput: string, password: string): Promise<{ ok: boolean; error?: string }> {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ email: emailInput, password }),
    })
    if (res.ok) {
      const data = (await res.json()) as { ok: boolean; email: string }
      email.value = data.email
      authMethod.value = "local_dev"
      isAuthenticated.value = true
      checked.value = true
      return { ok: true }
    }
    const err = (await res.json()) as { error: string }
    return { ok: false, error: err.error ?? "Login failed" }
  }

  async function logout() {
    await fetch("/api/auth/logout", { method: "POST", credentials: "include" })
    email.value = null
    authMethod.value = null
    isAuthenticated.value = false
  }

  return { email, authMethod, checked, isAuthenticated, fetchMe, login, logout }
})
