import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, Lock, Mail, AlertCircle, ShieldCheck } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export default function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!email || !password) {
      setError('Please fill in all fields.')
      return
    }

    setIsLoading(true)
    try {
      await login(email, password)
      navigate('/dashboard')
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      if (detail === 'Invalid credentials') {
        setError('Invalid email or password.')
      } else if (err?.code === 'ERR_NETWORK') {
        setError('Cannot reach server. Is the backend running?')
      } else {
        setError(detail ?? 'Something went wrong. Please try again.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex">
      {/* ── Left panel — branding ─────────────────────────────── */}
      <div className="hidden lg:flex lg:w-1/2 relative flex-col justify-between p-12 overflow-hidden">
        {/* Grid background */}
        <div className="absolute inset-0 grid-overlay opacity-30" />
        {/* Glow orb */}
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full bg-cyan-500/10 blur-3xl pointer-events-none" />

        {/* Logo */}
        <div className="relative z-10 flex items-center gap-3">
          <div className="w-8 h-8 rounded border border-cyan-500/40 bg-cyan-500/10 flex items-center justify-center">
            <ShieldCheck className="w-4 h-4 text-cyan-400" />
          </div>
          <span className="font-display font-bold text-sm tracking-widest uppercase text-foreground">
            ShardVault
          </span>
        </div>

        {/* Center copy */}
        <div className="relative z-10 space-y-6">
          <div className="space-y-2">
            <p className="font-mono text-xs text-cyan-400 tracking-widest uppercase">
              AES-256-GCM · Shamir Secret Sharing
            </p>
            <h1 className="font-display text-5xl font-extrabold leading-tight text-foreground">
              Your secrets,<br />
              <span className="text-cyan-400 glow-text">sharded.</span>
            </h1>
          </div>
          <p className="text-muted-foreground text-sm leading-relaxed max-w-sm">
            Threshold-secured vault. No single point of failure.
            Your master password never leaves your device.
          </p>

          {/* Feature pills */}
          <div className="flex flex-wrap gap-2 pt-2">
            {['N=4 shares', 'K=3 threshold', 'Zero-knowledge', 'HttpOnly cookies'].map((f) => (
              <span
                key={f}
                className="font-mono text-xs px-3 py-1 rounded border border-cyan-500/20 bg-cyan-500/5 text-cyan-400/80"
              >
                {f}
              </span>
            ))}
          </div>
        </div>

        {/* Bottom */}
        <div className="relative z-10">
          <p className="text-xs text-muted-foreground font-mono">
            © {new Date().getFullYear()} ShardVault · Built with FastAPI + React
          </p>
        </div>
      </div>

      {/* ── Right panel — form ────────────────────────────────── */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 lg:p-12">
        <div className="w-full max-w-sm space-y-8 page-enter">

          {/* Mobile logo */}
          <div className="flex lg:hidden items-center gap-2 mb-2">
            <ShieldCheck className="w-5 h-5 text-cyan-400" />
            <span className="font-display font-bold text-sm tracking-widest uppercase">ShardVault</span>
          </div>

          {/* Header */}
          <div className="space-y-1">
            <h2 className="font-display text-2xl font-bold text-foreground">Welcome back</h2>
            <p className="text-sm text-muted-foreground">
              Sign in to access your vault
            </p>
          </div>

          {/* Error banner */}
          {error && (
            <div className="flex items-start gap-3 rounded-md border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive animate-fade-in">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Email */}
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="pl-9"
                  disabled={isLoading}
                />
              </div>
            </div>

            {/* Password */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password">Password</Label>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pl-9 pr-10"
                  disabled={isLoading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Submit */}
            <Button
              type="submit"
              size="lg"
              className="w-full"
              disabled={isLoading}
            >
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <span className="w-4 h-4 rounded-full border-2 border-primary-foreground border-t-transparent animate-spin" />
                  Signing in...
                </span>
              ) : (
                'Sign in'
              )}
            </Button>
          </form>

          {/* Divider */}
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border" />
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="bg-background px-3 text-muted-foreground font-mono">
                no account?
              </span>
            </div>
          </div>

          {/* Register link */}
          <Button asChild variant="outline" size="lg" className="w-full">
            <Link to="/register">Create an account</Link>
          </Button>

          {/* Security note */}
          <p className="text-center text-xs text-muted-foreground font-mono leading-relaxed">
            Access tokens stored in memory only.
            <br />
            Refresh token delivered via HttpOnly cookie.
          </p>
        </div>
      </div>
    </div>
  )
}