import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Vault, Cpu, GitBranch, ChevronRight } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { vaultApi } from '@/api/vault'
import { apiClient } from '@/api/client'  // adjust to your actual axios/fetch instance
import { Badge } from '@/components/ui/badge'

type NodeHealth = { node_id: string; url: string; online: boolean }

type SystemStatus = {
  coordinator: 'online' | 'offline'
  nodes: NodeHealth[]
  nodesOnline: number
}

export default function DashboardPage() {
  const { user } = useAuth()
  const [vaultCount, setVaultCount] = useState<number | null>(null)
  const [system, setSystem] = useState<SystemStatus | null>(null)

  useEffect(() => {
    vaultApi.list(1, 1)
      .then(r => setVaultCount(r.total))
      .catch(() => setVaultCount(0))
  }, [])

  useEffect(() => {
    apiClient.get('/admin/nodes/health')
  .then(r => {
    const nodes: NodeHealth[] = r.data.nodes  // ← .nodes not r.data directly
    setSystem({
      coordinator: 'online',
      nodes,
      nodesOnline: nodes.filter(n => n.online).length,
    })
  })
      .catch(() => {
        setSystem({
          coordinator: 'offline',
          nodes: [],
          nodesOnline: 0,
        })
      })
  }, [])

  const stats = [
    { label: 'Vault entries',  value: vaultCount ?? '—',                          sub: 'encrypted secrets' },
    { label: 'Shamir shares',  value: vaultCount != null ? vaultCount * 4 : '—',  sub: 'N=4 per entry' },
    { label: 'Threshold',      value: 'K=3',                                       sub: 'min shares to reconstruct' },
    { label: 'Encryption',     value: 'AES-256',                                   sub: 'GCM authenticated' },
  ]

  const nodesOnline  = system?.nodesOnline ?? 0
  const nodeStatus   = system == null ? 'checking' : nodesOnline === 4 ? 'online' : nodesOnline > 0 ? 'degraded' : 'offline'
  const nodeDetail   = system == null ? 'Checking...' : `${nodesOnline}/4 nodes online`
  const coordDetail  = system == null ? 'Checking...' : system.coordinator === 'online' ? 'Connected' : 'Unreachable'

  const systemRows = [
    { label: 'Coordinator API', status: system?.coordinator ?? 'offline', detail: coordDetail },
    { label: 'Share Node 1–4',  status: nodeStatus,                       detail: nodeDetail },
    { label: 'Database',        status: 'online' as const,                 detail: 'Supabase PostgreSQL' },
  ]

  const badgeVariant = (s: string) => {
    if (s === 'online')    return 'success'
    if (s === 'degraded')  return 'warning'
    if (s === 'checking')  return 'secondary'
    return 'warning'
  }

  const dotColor = (s: string) => {
    if (s === 'online')   return 'bg-emerald-400'
    if (s === 'degraded') return 'bg-amber-400'
    if (s === 'checking') return 'bg-slate-400'
    return 'bg-amber-400'
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-8 page-enter">

      {/* Welcome */}
      <div className="space-y-1">
        <p className="font-mono text-xs text-cyan-400 tracking-widest uppercase">Overview</p>
        <h1 className="font-display text-2xl font-bold">
          Welcome back{user?.email ? `, ${user.email.split('@')[0]}` : ''}
        </h1>
        <p className="text-sm text-muted-foreground">
          Your distributed vault is secured across 4 independent share nodes.
        </p>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {stats.map(({ label, value, sub }) => (
          <div key={label} className="glass rounded-lg p-4 space-y-1">
            <p className="text-2xl font-display font-bold text-foreground">{value}</p>
            <p className="text-xs font-medium text-foreground">{label}</p>
            <p className="text-[10px] text-muted-foreground font-mono">{sub}</p>
          </div>
        ))}
      </div>

      {/* Quick actions */}
      <div className="space-y-3">
        <p className="text-xs font-mono text-muted-foreground uppercase tracking-widest">Quick actions</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">

          <Link to="/vault" className="glass rounded-lg p-5 flex items-center gap-4 hover:border-cyan-500/30 transition-all group">
            <div className="w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center shrink-0">
              <Vault className="w-5 h-5 text-cyan-400" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-sm">Vault</p>
              <p className="text-xs text-muted-foreground">Manage your encrypted entries</p>
            </div>
            <ChevronRight className="w-4 h-4 text-muted-foreground group-hover:text-cyan-400 transition-colors" />
          </Link>

          <div className="glass rounded-lg p-5 flex items-center gap-4 opacity-50 cursor-not-allowed">
            <div className="w-10 h-10 rounded-lg bg-secondary border border-border flex items-center justify-center shrink-0">
              <Cpu className="w-5 h-5 text-muted-foreground" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-sm">Crypto Engine</p>
              <p className="text-xs text-muted-foreground">Coming in Module 4</p>
            </div>
            <Badge variant="secondary" className="text-[10px]">Soon</Badge>
          </div>

        </div>
      </div>

      {/* System status */}
      <div className="space-y-3">
        <p className="text-xs font-mono text-muted-foreground uppercase tracking-widest">System</p>
        <div className="glass rounded-lg divide-y divide-border">
          {systemRows.map(({ label, status, detail }) => (
            <div key={label} className="flex items-center justify-between px-4 py-3">
              <div className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${dotColor(status)} animate-pulse_slow`} />
                <p className="text-sm font-medium">{label}</p>
              </div>
              <div className="flex items-center gap-2">
                <p className="text-xs text-muted-foreground font-mono">{detail}</p>
                <Badge variant={badgeVariant(status) as any}>{status}</Badge>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Branch indicator */}
      <div className="flex items-center gap-2 text-xs text-muted-foreground font-mono">
        <GitBranch className="w-3.5 h-3.5" />
        feature/frontend-vault
      </div>

    </div>
  )
}