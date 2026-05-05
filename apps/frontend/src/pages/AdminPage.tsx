/**
 * pages/AdminPage.tsx — ShardVault Admin Dashboard
 * Covers: node health cards, system stats, user table, audit log viewer
 */

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { adminApi } from "@/api/admin"
import { Shield, Users, Vault, Activity, Wifi, WifiOff, RefreshCw } from "lucide-react"

// ─── Helpers ──────────────────────────────────────────────────────────────────

function StatCard({ icon: Icon, label, value, sub }: {
  icon: React.ElementType
  label: string
  value: string | number
  sub?: string
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-5 flex flex-col gap-3">
      <div className="flex items-center gap-2 text-muted-foreground text-xs font-mono uppercase tracking-widest">
        <Icon className="w-4 h-4" />
        {label}
      </div>
      <p className="text-3xl font-bold text-foreground">{value}</p>
      {sub && <p className="text-xs text-muted-foreground">{sub}</p>}
    </div>
  )
}

function NodeCard({ node }: { node: { node_id: string; url: string; status: string; latency_ms: number | null } }) {
  const online = node.status === "online"
  return (
    <div className={`rounded-xl border p-4 flex flex-col gap-2 ${online ? "border-green-500/30 bg-green-500/5" : "border-red-500/30 bg-red-500/5"}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-mono text-muted-foreground uppercase tracking-widest">{node.node_id}</span>
        {online
          ? <Wifi className="w-4 h-4 text-green-500" />
          : <WifiOff className="w-4 h-4 text-red-500" />}
      </div>
      <p className={`text-sm font-semibold ${online ? "text-green-400" : "text-red-400"}`}>
        {online ? "Online" : "Offline"}
      </p>
      <p className="text-xs text-muted-foreground font-mono truncate">{node.url}</p>
      {node.latency_ms != null && (
        <p className="text-xs text-muted-foreground">{node.latency_ms} ms</p>
      )}
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function AdminPage() {
  const [auditFilter, setAuditFilter] = useState("")

  const stats = useQuery({
    queryKey: ["admin", "stats"],
    queryFn: adminApi.getStats,
    refetchInterval: 30_000,
  })

  const users = useQuery({
    queryKey: ["admin", "users"],
    queryFn: () => adminApi.getUsers(1, 20),
  })

  const nodes = useQuery({
    queryKey: ["admin", "nodes"],
    queryFn: adminApi.getNodesHealth,
    refetchInterval: 15_000,
  })


  const totalAuditEvents = stats.data
    ? Object.values(stats.data.audit_event_counts).reduce((a, b) => a + b, 0)
    : 0

  return (
    <div className="p-6 space-y-8 max-w-7xl mx-auto">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
            <Shield className="w-6 h-6 text-primary" /> Admin Dashboard
          </h1>
          <p className="text-sm text-muted-foreground mt-1">System overview and node health</p>
        </div>
        <button
          onClick={() => { stats.refetch(); nodes.refetch(); users.refetch() }}
          className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground border border-border rounded-lg px-3 py-2 transition-colors"
        >
          <RefreshCw className="w-3 h-3" /> Refresh
        </button>
      </div>

      {/* Stat Cards */}
      <section>
        <h2 className="text-xs font-mono uppercase tracking-widest text-muted-foreground mb-3">System Stats</h2>
        {stats.isLoading ? (
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-28 rounded-xl border border-border bg-card animate-pulse" />
            ))}
          </div>
        ) : stats.isError ? (
          <p className="text-sm text-red-400">Failed to load stats.</p>
        ) : (
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
            <StatCard icon={Users} label="Total Users" value={stats.data!.total_users} />
            <StatCard icon={Vault} label="Total Vaults" value={stats.data!.total_vault_entries} />
            <StatCard
              icon={Activity}
              label="Audit Events"
              value={totalAuditEvents}
              sub={Object.entries(stats.data!.audit_event_counts)
                .map(([k, v]) => `${k}: ${v}`)
                .join(" · ")}
            />
          </div>
        )}
      </section>

      {/* Node Health */}
      <section>
        <h2 className="text-xs font-mono uppercase tracking-widest text-muted-foreground mb-3">
          Share Nodes — Distributed Architecture
        </h2>
        {nodes.isLoading ? (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-28 rounded-xl border border-border bg-card animate-pulse" />
            ))}
          </div>
        ) : nodes.isError ? (
          <p className="text-sm text-red-400">Failed to reach node health endpoint.</p>
        ) : (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {nodes.data!.nodes.map((node) => (
              <NodeCard key={node.node_id} node={node} />
            ))}
          </div>
        )}
      </section>

      {/* User Table */}
      <section>
        <h2 className="text-xs font-mono uppercase tracking-widest text-muted-foreground mb-3">Users</h2>
        {users.isLoading ? (
          <div className="h-40 rounded-xl border border-border bg-card animate-pulse" />
        ) : users.isError ? (
          <p className="text-sm text-red-400">Failed to load users.</p>
        ) : (
          <div className="rounded-xl border border-border overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted/40">
                <tr>
                  {["Email", "Role", "Vaults", "Joined"].map((h) => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-mono uppercase tracking-widest text-muted-foreground">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {users.data!.users.map((u, i) => (
                  <tr
                    key={u.id}
                    className={`border-t border-border ${i % 2 === 0 ? "" : "bg-muted/20"}`}
                  >
                    <td className="px-4 py-3 font-mono text-xs text-foreground">{u.email}</td>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-mono ${u.role === "admin" ? "bg-primary/20 text-primary" : "bg-muted text-muted-foreground"}`}>
                        {u.role}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">{u.vault_count}</td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Audit Log Viewer */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-mono uppercase tracking-widest text-muted-foreground">
            Recent Audit Events
          </h2>
          <select
            value={auditFilter}
            onChange={(e) => setAuditFilter(e.target.value)}
            className="text-xs bg-card border border-border rounded-lg px-3 py-1.5 text-foreground"
          >
            <option value="">All Actions</option>
            {stats.data && Object.keys(stats.data.audit_event_counts).map((action) => (
              <option key={action} value={action}>{action}</option>
            ))}
          </select>
        </div>
        <div className="rounded-xl border border-border p-4 text-xs text-muted-foreground font-mono">
          {/* Wire this to GET /audit-logs once backend Module 8 is done */}
          <p className="text-center py-6">Audit log viewer will be wired to <span className="text-primary">GET /audit-logs</span> after Module 8 backend is deployed.</p>
        </div>
      </section>

    </div>
  )
}