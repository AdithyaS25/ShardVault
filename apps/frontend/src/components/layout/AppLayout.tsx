import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  ShieldCheck, Vault, LogOut, Menu, X,
  Settings, LayoutDashboard, ChevronRight,
  Activity, ShieldAlert,
} from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

const NAV = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Overview'     },
  { to: '/vault',     icon: Vault,           label: 'Vault'        },
  { to: '/audit',     icon: Activity,        label: 'Activity Log' },
  { to: '/settings',  icon: Settings,        label: 'Settings'     },
]

export default function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen flex bg-background">

      {/* ── Mobile overlay ──────────────────────────────────── */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/60 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* ── Sidebar ─────────────────────────────────────────── */}
      <aside className={cn(
        'fixed top-0 left-0 z-30 h-full w-64 flex flex-col border-r border-border bg-card',
        'transition-transform duration-300 ease-in-out',
        'lg:translate-x-0 lg:static lg:z-auto',
        mobileOpen ? 'translate-x-0' : '-translate-x-full'
      )}>

        {/* Logo */}
        <div className="flex items-center justify-between px-5 py-5 border-b border-border">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded border border-cyan-500/40 bg-cyan-500/10 flex items-center justify-center shrink-0">
              <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
            </div>
            <span className="font-display font-bold text-sm tracking-widest uppercase">
              ShardVault
            </span>
          </div>
          <button
            className="lg:hidden text-muted-foreground hover:text-foreground"
            onClick={() => setMobileOpen(false)}
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setMobileOpen(false)}
              className={({ isActive }) => cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-all duration-150 group',
                isActive
                  ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                  : 'text-muted-foreground hover:text-foreground hover:bg-secondary'
              )}
            >
              {({ isActive }) => (
                <>
                  <Icon className={cn('w-4 h-4 shrink-0', isActive ? 'text-cyan-400' : '')} />
                  <span className="flex-1 font-medium">{label}</span>
                  {isActive && <ChevronRight className="w-3 h-3 text-cyan-400/60" />}
                </>
              )}
            </NavLink>
          ))}

          {/* Admin-only link */}
          {user?.role === 'admin' && (
            <NavLink
              to="/admin"
              onClick={() => setMobileOpen(false)}
              className={({ isActive }) => cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-all duration-150 group',
                isActive
                  ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                  : 'text-muted-foreground hover:text-foreground hover:bg-secondary'
              )}
            >
              {({ isActive }) => (
                <>
                  <ShieldAlert className={cn('w-4 h-4 shrink-0', isActive ? 'text-cyan-400' : '')} />
                  <span className="flex-1 font-medium">Admin</span>
                  {isActive && <ChevronRight className="w-3 h-3 text-cyan-400/60" />}
                </>
              )}
            </NavLink>
          )}
        </nav>

        {/* User section */}
        <div className="px-3 py-4 border-t border-border space-y-2">
          <div className="px-3 py-2.5 rounded-md bg-secondary/50 space-y-1">
            <p className="text-xs font-mono text-foreground truncate">{user?.email}</p>
            <Badge variant={user?.role === 'admin' ? 'default' : 'secondary'} className="text-[10px]">
              {user?.role}
            </Badge>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start gap-2 text-muted-foreground hover:text-destructive"
            onClick={handleLogout}
          >
            <LogOut className="w-4 h-4" />
            Sign out
          </Button>
        </div>
      </aside>

      {/* ── Main content ─────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0">

        {/* Mobile topbar */}
        <header className="lg:hidden flex items-center justify-between px-4 py-3 border-b border-border">
          <button
            className="text-muted-foreground hover:text-foreground"
            onClick={() => setMobileOpen(true)}
          >
            <Menu className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-cyan-400" />
            <span className="font-display font-bold text-sm tracking-widest uppercase">ShardVault</span>
          </div>
          <div className="w-5" />
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}