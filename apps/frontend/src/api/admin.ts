/**
 * api/admin.ts — ShardVault Frontend
 * Mirrors endpoints from app/admin/routes.py (Module 8)
 */

import apiClient from "./client"
import type {
  AdminStats,
  AdminUsersResponse,
  AdminUserDetail,
  NodesHealthResponse,
} from "@/types/admin"

export const adminApi = {
  /** GET /admin/stats — system-wide counts */
  getStats: async (): Promise<AdminStats> => {
    const res = await apiClient.get<AdminStats>("/admin/stats")
    return res.data
  },

  /** GET /admin/users — paginated user list */
  getUsers: async (page = 1, pageSize = 20): Promise<AdminUsersResponse> => {
    const res = await apiClient.get<AdminUsersResponse>("/admin/users", {
      params: { page, page_size: pageSize },
    })
    return res.data
  },

  /** GET /admin/users/:id — single user detail */
  getUserDetail: async (id: string): Promise<AdminUserDetail> => {
    const res = await apiClient.get<AdminUserDetail>(`/admin/users/${id}`)
    return res.data
  },

  /** GET /admin/nodes/health — live node health check */
  getNodesHealth: async (): Promise<NodesHealthResponse> => {
    const res = await apiClient.get<NodesHealthResponse>("/admin/nodes/health")
    return res.data
  },
}