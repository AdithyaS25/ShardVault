/**
 * pages/AuditPage.tsx — ShardVault
 * Shows the current user's own audit activity log
 * Endpoint: GET /audit-logs/me
 */

import { useState, useCallback, useEffect } from 'react'
import { Activity, AlertCircle, ChevronLeft, ChevronRight, Filter } from 'lucide-react'
import { auditApi, type AuditLogEntry } from '@/api/audit'
import { Button } from '@/components/ui/button'

// ── Helpers ───────────────────────────────────────────────────────────────────

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins  = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days  = Math.floor(diff / 86400000)
  if (mins < 1)   return 'just now'
  if (mins < 60)  return `${mins}m ago`
  if (hours < 24) return `${hours}h ago`
  return `${days}d ago`
}

// Map action strings to badge colours
function actionVariant(action: string): string {
  if (action.includes('login'))    return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20'
  if (action.includes('logout'))   return 'bg-secondary text-muted-foreground border-border'
  if (action.includes('create'))   return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
  if (action.includes('retrieve')) return 'bg-violet-500/10 text-violet-400 border-violet-500/20'
  if (action.includes('delete'))   return 'bg-red-500/10 text-red-400 border-red-500/20'
  if (action.includes('register')) return 'bg-amber-500/10 text-amber-400 border-amber-500/20'
  return 'bg-secondary text-muted-foreground border-border'
}

// ── Known action types for filter dropdown ────────────────────────────────────

const ACTION_FILTERS = [
  { label: 'All Actions', value: '' },
  { label: 'Login',       value: 'login' },
  { label: 'Logout',      value: 'logout' },
  { label: 'Register',    value: 'register' },
  { label: 'Vault Create',   value: 'vault_create' },
  { label: 'Vault Retrieve', value: 'vault_retrieve' },
  { label: 'Vault Delete',   value: 'vault_delete' },
]

// ── Log Row ───────────────────────────────────────────────────────────────────

function LogRow({ entry }: { entry: AuditLogEntry }) {
  return (
    <div className="glass rounded-lg px-4 py-3 flex items-center gap-4 animate-fade-in">
      <div className="flex-1 min-w-0 flex items-center gap-3">
        <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${actionVariant(entry.action)}`}>
          {entry.action}
        </span>
        {entry.ip_address && (
          <span className="text-xs text-muted-foreground font-mono hidden sm:block">
            {entry.ip_address}
          </span>
        )}
      </div>
      <p className="text-xs text-muted-foreground font-mono shrink-0">
        {timeAgo(entry.created_at)}
      </p>
    </div>
  )
}

// ── Empty State ───────────────────────────────────────────────────────────────

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-24 gap-5 text-center">
      <div className="w-16 h-16 rounded-2xl border border-border bg-secondary/50 flex items-center justify-center">
        <Activity className="w-7 h-7 text-muted-foreground" />
      </div>
      <div className="space-y-1">
        <p className="font-display font-semibold text-foreground">No activity yet</p>
        <p className="text-sm text-muted-foreground max-w-xs">
          Your login events, vault creates and retrieves will appear here.
        </p>
      </div>
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function AuditPage() {
  const [entries, setEntries]   = useState<AuditLogEntry[]>([])
  const [total, setTotal]       = useState(0)
  const [page, setPage]         = useState(1)
  const [action, setAction]     = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError]       = useState<string | null>(null)

  const PAGE_SIZE = 20

  const fetchLogs = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await auditApi.getMyLogs(page, PAGE_SIZE, action || undefined)
      setEntries(res.data)
      setTotal(res.total)
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? 'Failed to load audit logs.')
    } finally {
      setIsLoading(false)
    }
  }, [page, action])

  useEffect(() => { fetchLogs() }, [fetchLogs])

  // Reset to page 1 when filter changes
  const handleFilterChange = (value: string) => {
    setAction(value)
    setPage(1)
  }

  const totalPages = Math.ceil(total / PAGE_SIZE)

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6 page-enter">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold flex items-center gap-2">
            <Activity className="w-6 h-6 text-cyan-400" />
            Activity Log
          </h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {total} {total === 1 ? 'event' : 'events'} · your account activity history
          </p>
        </div>

        {/* Action filter */}
        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-muted-foreground" />
          <select
            value={action}
            onChange={e => handleFilterChange(e.target.value)}
            className="text-xs bg-card border border-border rounded-lg px-3 py-1.5 text-foreground focus:outline-none focus:ring-1 focus:ring-cyan-500/30"
          >
            {ACTION_FILTERS.map(f => (
              <option key={f.value} value={f.value}>{f.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-start gap-3 rounded-md border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
          {error}
        </div>
      )}

      {/* Content */}
      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="h-12 rounded-lg shimmer" />
          ))}
        </div>
      ) : entries.length === 0 ? (
        <EmptyState />
      ) : (
        <>
          <div className="space-y-2">
            {entries.map(entry => (
              <LogRow key={entry.id} entry={entry} />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-2">
              <p className="text-xs text-muted-foreground font-mono">
                Page {page} of {totalPages}
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="h-7 px-2 gap-1"
                  onClick={() => setPage(p => p - 1)}
                  disabled={page === 1}
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                  Prev
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="h-7 px-2 gap-1"
                  onClick={() => setPage(p => p + 1)}
                  disabled={page === totalPages}
                >
                  Next
                  <ChevronRight className="w-3.5 h-3.5" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}