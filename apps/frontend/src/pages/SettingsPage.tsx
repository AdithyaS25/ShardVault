/**
 * pages/SettingsPage.tsx — ShardVault
 * Account info display + security notes
 * No editable fields yet — profile is immutable (email set at registration)
 */

import { useState } from 'react'
import { Settings, Mail, ShieldCheck, KeyRound, AlertCircle, Loader2, LogOut } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

// ── Section wrapper ───────────────────────────────────────────────────────────

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-3">
      <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground">{title}</p>
      <div className="glass rounded-lg divide-y divide-border">
        {children}
      </div>
    </div>
  )
}

function Row({ icon: Icon, label, value, mono = false }: {
  icon: React.ElementType
  label: string
  value: React.ReactNode
  mono?: boolean
}) {
  return (
    <div className="flex items-center justify-between px-4 py-3">
      <div className="flex items-center gap-3">
        <Icon className="w-4 h-4 text-muted-foreground shrink-0" />
        <p className="text-sm font-medium">{label}</p>
      </div>
      <p className={`text-sm text-muted-foreground ${mono ? 'font-mono' : ''}`}>{value}</p>
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function SettingsPage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [isLoggingOut, setIsLoggingOut] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleLogout = async () => {
    setIsLoggingOut(true)
    setError(null)
    try {
      await logout()
      navigate('/login')
    } catch {
      setError('Logout failed. Please try again.')
      setIsLoggingOut(false)
    }
  }

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-8 page-enter">

      {/* Header */}
      <div>
        <h1 className="font-display text-2xl font-bold flex items-center gap-2">
          <Settings className="w-6 h-6 text-cyan-400" />
          Settings
        </h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Account information and security details
        </p>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-start gap-3 rounded-md border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
          {error}
        </div>
      )}

      {/* Account */}
      <Section title="Account">
        <Row
          icon={Mail}
          label="Email"
          value={user?.email ?? '—'}
          mono
        />
        <Row
          icon={ShieldCheck}
          label="Role"
          value={
            <Badge variant={user?.role === 'admin' ? 'default' : 'secondary'} className="text-[10px]">
              {user?.role}
            </Badge>
          }
        />
        <Row
          icon={KeyRound}
          label="User ID"
          value={user?.id ? `${user.id.slice(0, 8)}…` : '—'}
          mono
        />
      </Section>

      {/* Security */}
      <Section title="Security">
        <Row icon={ShieldCheck} label="Encryption"      value="AES-256-GCM"        mono />
        <Row icon={ShieldCheck} label="Key derivation"  value="Argon2id"            mono />
        <Row icon={ShieldCheck} label="Secret sharing"  value="Shamir N=4 / K=3"   mono />
        <Row icon={ShieldCheck} label="Access token"    value="In-memory only"      mono />
        <Row icon={ShieldCheck} label="Refresh token"   value="HttpOnly cookie"     mono />
        <Row icon={ShieldCheck} label="Master password" value="Never stored or sent" mono />
      </Section>

      {/* Session */}
      <Section title="Session">
        <div className="px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <LogOut className="w-4 h-4 text-muted-foreground shrink-0" />
            <div>
              <p className="text-sm font-medium">Sign out</p>
              <p className="text-xs text-muted-foreground">
                Revokes your refresh token and clears session
              </p>
            </div>
          </div>
          <Button
            variant="destructive"
            size="sm"
            onClick={handleLogout}
            disabled={isLoggingOut}
          >
            {isLoggingOut ? (
              <span className="flex items-center gap-1.5">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Signing out...
              </span>
            ) : 'Sign out'}
          </Button>
        </div>
      </Section>

      {/* Footer note */}
      <p className="text-center text-xs text-muted-foreground font-mono leading-relaxed">
        Access tokens stored in memory only.
        <br />
        Refresh token delivered via HttpOnly cookie.
      </p>

    </div>
  )
}