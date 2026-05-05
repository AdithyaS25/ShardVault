/**
 * api/audit.ts — ShardVault Frontend
 * Mirrors GET /audit-logs/me from backend Module 7
 */

import { apiClient } from './client'

export interface AuditLogEntry {
  id: string
  action: string
  ip_address: string | null
  created_at: string
}

export interface AuditLogResponse {
  success: boolean
  data: AuditLogEntry[]
  total: number
  page: number
  page_size: number
}

export const auditApi = {
  /** GET /audit-logs/me — current user's own activity */
  getMyLogs: async (
    page = 1,
    page_size = 20,
    action?: string
  ): Promise<AuditLogResponse> => {
    const { data } = await apiClient.get<AuditLogResponse>('/audit-logs/me', {
      params: { page, page_size, ...(action ? { action } : {}) },
    })
    return data
  },
}