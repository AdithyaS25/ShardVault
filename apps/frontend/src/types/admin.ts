// ─── Admin ───────────────────────────────────────────────────────────────────

export interface AdminStats {
  total_users: number
  total_vault_entries: number
  audit_event_counts: Record<string, number>
}

export interface AdminUser {
  id: string
  email: string
  role: "user" | "admin"
  vault_count: number
  created_at: string
}

export interface AdminUsersResponse {
  users: AdminUser[]
  total: number
  page: number
  page_size: number
}

export interface AdminUserDetail extends AdminUser {
  recent_audit: AuditEvent[]
}

export interface NodeHealth {
  node_id: string
  url: string
  status: "online" | "offline"
  latency_ms: number | null
}

export interface NodesHealthResponse {
  nodes: NodeHealth[]
}

export interface AuditEvent {
  id: string
  user_id: string
  action: string
  ip_address?: string
  created_at: string
}