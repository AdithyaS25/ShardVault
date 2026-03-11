/**
 * api/auth.ts — ShardVault Frontend
 * Mirrors endpoints from app/auth/routes.py
 */

import apiClient from "./client"
import type {
  RegisterRequest,
  RegisterResponse,
  LoginRequest,
  LoginResponse,
  LogoutResponse,
  MeResponse,
} from "@/types"

export const authApi = {
  /** POST /auth/register */
  register: async (data: RegisterRequest): Promise<RegisterResponse> => {
    const res = await apiClient.post<RegisterResponse>("/auth/register", data)
    return res.data
  },

  /** POST /auth/login — refresh token set as HttpOnly cookie by server */
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const res = await apiClient.post<LoginResponse>("/auth/login", data)
    return res.data
  },

  /** POST /auth/refresh — reads HttpOnly cookie automatically */
  refresh: async (): Promise<LoginResponse> => {
    const res = await apiClient.post<LoginResponse>("/auth/refresh")
    return res.data
  },

  /** POST /auth/logout — revokes HttpOnly cookie */
  logout: async (): Promise<LogoutResponse> => {
    const res = await apiClient.post<LogoutResponse>("/auth/logout")
    return res.data
  },

  /** GET /auth/me — requires Bearer token */
  me: async (): Promise<MeResponse> => {
    const res = await apiClient.get<MeResponse>("/auth/me")
    return res.data
  },

  /** POST /auth/create-admin — admin only */
  createAdmin: async (data: RegisterRequest): Promise<{ message: string }> => {
    const res = await apiClient.post<{ message: string }>("/auth/create-admin", data)
    return res.data
  },
}
