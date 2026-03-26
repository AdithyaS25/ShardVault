import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, Lock, Mail, AlertCircle, ShieldCheck, CheckCircle2, XCircle } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

// ── Password strength rules ───────────────────────────────────────────────────
const RULES = [
  { id: 'length',  label: 'At least 8 characters',     test: (p: string) => p.length >= 8 },
  { id: 'upper',   label: 'One uppercase letter',       test: (p: string) => /[A-Z]/.test(p) },
  { id: 'lower',   label: 'One lowercase letter',       test: (p: string) => /[a-z]/.test(p) },
  { id: 'number',  label: 'One number',                 test: (p: string) => /\d/.test(p) },
]

function PasswordStrength({ password }: { password: string }) {
  if (!password) return null
  const passed = RULES.filter((r) => r.test(password)).length
  const strength = passed <= 1 ? 'Weak' : passed <= 3 ? 'Fair' : 'Strong'
  const color = passed <= 1 ? 'bg-destructive' : passed <= 3 ? 'bg-amber-500' : 'bg-emerald-500'

  return (
    <div className="space-y-2 pt-1 animate-fade-in">
      {/* Bar */}
      <div className="flex gap-1">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className={`h-1 flex-1 rounded-full transition-all duration-300 ${
              i <= passed ? color : 'bg-border'
            }`}
          />
        ))}
      </div>
      <p className="text-xs text-muted-foreground font-mono">Strength: <span className="text-foreground">{strength}</span></p>
      {/* Rules */}
      <ul className="space-y-1">
        {RULES.map((rule) => {
          const ok = rule.test(password)
          return (
            <li key={rule.id} className="flex items-center gap-2 text-xs">
              {ok
                ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                : <XCircle className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
              }
              <span className={ok ? 'text-foreground' : 'text-muted-foreground'}>
                {rule.label}
              </span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

export default function RegisterPage() {
  const navigate = useNavigate()
  const { register } = useAuth()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const passwordsMatch = confirmPassword ? password === confirmPassword : null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!email || !password || !confirmPassword) {
      setError('Please fill in all fields.')
      return
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setIsLoading(true)
    try {
      await register(email, password)
      navigate('/dashboard')
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      if (detail === 'Email already registered') {
        setError('This email is already registered. Try logging in.')
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
        <div className="absolute inset-0 grid-overlay opacity-30" />
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
              Distributed · Encrypted · Threshold-secured
            </p>
            <h1 className="font-display text-5xl font-extrabold leading-tight text-foreground">
              One vault.<br />
              <span className="text-cyan-400 glow-text">Four shards.</span>
            </h1>
          </div>
          <p className="text-muted-foreground text-sm leading-relaxed max-w-sm">
            Your encrypted secret is split into 4 shares across independent nodes.
            Any 3 can reconstruct it. No single node holds the full picture.
          </p>

          {/* How it works */}
          <div className="space-y-3 pt-2">
            {[
              { step: '01', text: 'Register & set your master password' },
              { step: '02', text: 'Secrets encrypted with AES-256-GCM' },
              { step: '03', text: 'Shamir splits into 4 distributed shares' },
            ].map(({ step, text }) => (
              <div key={step} className="flex items-center gap-4">
                <span className="font-mono text-xs text-cyan-400/60 w-6 shrink-0">{step}</span>
                <span className="text-sm text-muted-foreground">{text}</span>
              </div>
            ))}
          </div>
        </div>

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
          <div className="flex lg:hidden items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-cyan-400" />
            <span className="font-display font-bold text-sm tracking-widest uppercase">ShardVault</span>
          </div>

          {/* Header */}
          <div className="space-y-1">
            <h2 className="font-display text-2xl font-bold text-foreground">Create account</h2>
            <p className="text-sm text-muted-foreground">
              Set up your distributed vault
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
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  autoComplete="new-password"
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
              <PasswordStrength password={password} />
            </div>

            {/* Confirm Password */}
            <div className="space-y-2">
              <Label htmlFor="confirm">Confirm password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  id="confirm"
                  type={showConfirm ? 'text' : 'password'}
                  placeholder="••••••••"
                  autoComplete="new-password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className={`pl-9 pr-10 ${
                    passwordsMatch === false
                      ? 'border-destructive/50 focus-visible:ring-destructive/50'
                      : passwordsMatch === true
                      ? 'border-emerald-500/50 focus-visible:ring-emerald-500/50'
                      : ''
                  }`}
                  disabled={isLoading}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm(!showConfirm)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  tabIndex={-1}
                >
                  {showConfirm ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {passwordsMatch === false && (
                <p className="text-xs text-destructive font-mono animate-fade-in">
                  Passwords do not match
                </p>
              )}
              {passwordsMatch === true && (
                <p className="text-xs text-emerald-400 font-mono animate-fade-in">
                  ✓ Passwords match
                </p>
              )}
            </div>

            {/* Submit */}
            <Button
              type="submit"
              size="lg"
              className="w-full"
              disabled={isLoading || passwordsMatch === false}
            >
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <span className="w-4 h-4 rounded-full border-2 border-primary-foreground border-t-transparent animate-spin" />
                  Creating vault...
                </span>
              ) : (
                'Create account'
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
                have an account?
              </span>
            </div>
          </div>

          {/* Login link */}
          <Button asChild variant="outline" size="lg" className="w-full">
            <Link to="/login">Sign in instead</Link>
          </Button>

          {/* Security note */}
          <p className="text-center text-xs text-muted-foreground font-mono leading-relaxed">
            Your master password is never stored or transmitted.
            <br />
            Encryption happens client-side before any network call.
          </p>
        </div>
      </div>
    </div>
  )
}