import { useAuth } from '@/context/AuthContext'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ShieldCheck, LogOut, Lock, Cpu, GitBranch } from 'lucide-react'

export default function DashboardPage() {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen flex flex-col page-enter">
      {/* ── Top nav ───────────────────────────────────────────── */}
      <header className="border-b border-border px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded border border-cyan-500/40 bg-cyan-500/10 flex items-center justify-center">
            <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <span className="font-display font-bold text-sm tracking-widest uppercase">ShardVault</span>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-2">
            <span className="text-xs text-muted-foreground font-mono">{user?.email}</span>
            <Badge variant={user?.role === 'admin' ? 'default' : 'secondary'}>
              {user?.role}
            </Badge>
          </div>
          <Button variant="ghost" size="icon" onClick={logout} title="Logout">
            <LogOut className="w-4 h-4" />
          </Button>
        </div>
      </header>

      {/* ── Main ──────────────────────────────────────────────── */}
      <main className="flex-1 flex flex-col items-center justify-center gap-8 p-6">
        <div className="text-center space-y-3">
          <p className="font-mono text-xs text-cyan-400 tracking-widest uppercase animate-pulse_slow">
            Module 2 complete
          </p>
          <h1 className="font-display text-3xl font-bold">Auth is working ✓</h1>
          <p className="text-sm text-muted-foreground">
            Logged in as <span className="text-primary font-mono">{user?.email}</span>
          </p>
        </div>

        {/* Module status cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 w-full max-w-2xl">
          {[
            { icon: ShieldCheck, label: 'Auth', status: 'Complete', module: 'M2', done: true },
            { icon: Lock,        label: 'Vault',  status: 'Next up',  module: 'M3', done: false },
            { icon: Cpu,         label: 'Crypto', status: 'Planned',  module: 'M4', done: false },
          ].map(({ icon: Icon, label, status, module, done }) => (
            <div
              key={label}
              className={`glass rounded-lg p-5 space-y-3 ${done ? 'border-cyan-500/20' : ''}`}
            >
              <div className="flex items-center justify-between">
                <Icon className={`w-5 h-5 ${done ? 'text-cyan-400' : 'text-muted-foreground'}`} />
                <span className="font-mono text-xs text-muted-foreground">{module}</span>
              </div>
              <div>
                <p className="font-medium text-sm">{label}</p>
                <p className={`text-xs font-mono ${done ? 'text-cyan-400' : 'text-muted-foreground'}`}>
                  {status}
                </p>
              </div>
            </div>
          ))}
        </div>

        <div className="flex items-center gap-2 text-xs text-muted-foreground font-mono">
          <GitBranch className="w-3.5 h-3.5" />
          <span>feature/frontend-auth</span>
        </div>
      </main>
    </div>
  )
}