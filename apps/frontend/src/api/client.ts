/**
 * api/client.ts — ShardVault Frontend
 * =====================================
 * Axios instance with:
 *   - Base URL from VITE_API_BASE_URL env var
 *   - Access token injected from memory (never localStorage)
 *   - Automatic silent refresh on 401 (single retry)
 *   - Credentials: true for HttpOnly refresh cookie
 *
 * Security rules (per §1.6):
 *   - Access token lives ONLY in memory (module-level variable)
 *   - Refresh token is HttpOnly cookie — never touched by JS
 *   - No decrypted passwords ever stored here
 */

import axios, { type AxiosRequestConfig, type InternalAxiosRequestConfig } from "axios"

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1"

// ── In-memory token store (§1.6: no localStorage) ────────────────────────────
let _accessToken: string | null = null

export const tokenStore = {
  get: () => _accessToken,
  set: (token: string | null) => { _accessToken = token },
  clear: () => { _accessToken = null },
}

// ── Axios instance ────────────────────────────────────────────────────────────
export const apiClient = axios.create({
  baseURL: BASE_URL,
  withCredentials: true, // Required: sends HttpOnly refresh cookie
  headers: {
    "Content-Type": "application/json",
  },
})

// ── Request interceptor — attach Bearer token ─────────────────────────────────
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = tokenStore.get()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ── Response interceptor — silent refresh on 401 ─────────────────────────────
let _isRefreshing = false
let _failedQueue: Array<{
  resolve: (value: unknown) => void
  reject: (reason?: unknown) => void
  config: AxiosRequestConfig
}> = []

const processQueue = (error: unknown, token: string | null) => {
  _failedQueue.forEach(({ resolve, reject, config }) => {
    if (error) {
      reject(error)
    } else {
      if (config.headers) {
        (config.headers as Record<string, string>).Authorization = `Bearer ${token}`
      }
      resolve(apiClient(config))
    }
  })
  _failedQueue = []
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean }

    // Only retry once, only on 401, skip refresh endpoint itself
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes("/auth/refresh") &&
      !originalRequest.url?.includes("/auth/login")
    ) {
      if (_isRefreshing) {
        // Queue requests while refreshing
        return new Promise((resolve, reject) => {
          _failedQueue.push({ resolve, reject, config: originalRequest })
        })
      }

      originalRequest._retry = true
      _isRefreshing = true

      try {
        const { data } = await axios.post(
          `${BASE_URL}/auth/refresh`,
          {},
          { withCredentials: true }
        )
        const newToken = data.access_token
        tokenStore.set(newToken)
        processQueue(null, newToken)

        if (originalRequest.headers) {
          (originalRequest.headers as Record<string, string>).Authorization = `Bearer ${newToken}`
        }
        return apiClient(originalRequest)
      } catch (refreshError) {
        tokenStore.clear()
        processQueue(refreshError, null)
        // Redirect to login on hard auth failure
        window.location.href = "/login"
        return Promise.reject(refreshError)
      } finally {
        _isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

export default apiClient
