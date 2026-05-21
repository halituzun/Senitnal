import { ref, type Ref } from "vue"

export function useFetch<T>(url: string, options?: RequestInit) {
  const data: Ref<T | null> = ref(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function execute(overrideUrl?: string | Event) {
    loading.value = true
    error.value = null
    try {
      const urlToFetch = typeof overrideUrl === "string" ? overrideUrl : url
      const res = await fetch(urlToFetch, { credentials: "include", ...options })
      if (!res.ok) {
        const body = (await res.json()) as { error?: string }
        error.value = body.error ?? `HTTP ${res.status}`
      } else {
        data.value = (await res.json()) as T
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Network error"
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, execute }
}
