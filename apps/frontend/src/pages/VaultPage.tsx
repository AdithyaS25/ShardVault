import { useState, useEffect, useCallback } from 'react'
import {
  Plus, Search, Eye, EyeOff, Trash2, Globe,
  User, Tag, Lock, Copy, Check, AlertCircle,
  ShieldAlert, Loader2, KeyRound, X,
} from 'lucide-react'
import { vaultApi, type VaultEntryMeta } from '@/api/vault'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'

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

function getInitials(name: string): string {
  return name.slice(0, 2).toUpperCase()
}

// ── Subcomponents ─────────────────────────────────────────────────────────────

function EmptyState({ onAdd }: { onAdd: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-24 gap-5 text-center">
      <div className="w-16 h-16 rounded-2xl border border-border bg-secondary/50 flex items-center justify-center">
        <KeyRound className="w-7 h-7 text-muted-foreground" />
      </div>
      <div className="space-y-1">
        <p className="font-display font-semibold text-foreground">No vault entries yet</p>
        <p className="text-sm text-muted-foreground max-w-xs">
          Add your first password. It will be encrypted and split into 4 Shamir shares.
        </p>
      </div>
      <Button onClick={onAdd} size="sm" className="gap-2">
        <Plus className="w-4 h-4" />
        Add first entry
      </Button>
    </div>
  )
}

function NodeUnavailableBanner() {
  return (
    <div className="flex items-start gap-3 rounded-md border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-400 mb-6">
      <ShieldAlert className="w-4 h-4 mt-0.5 shrink-0" />
      <div>
        <p className="font-medium">Share nodes unavailable</p>
        <p className="text-xs text-amber-400/70 mt-0.5">
          Vault create/retrieve operations require share nodes to be running.
          List and delete metadata operations still work.
        </p>
      </div>
    </div>
  )
}

// ── Create Modal ──────────────────────────────────────────────────────────────

interface CreateModalProps {
  onClose: () => void
  onCreated: () => void
}

function CreateModal({ onClose, onCreated }: CreateModalProps) {
  const [form, setForm] = useState({
    site_name: '', username: '', label: '',
    plaintext_password: '', master_password: '',
  })
  const [showPass, setShowPass]     = useState(false)
  const [showMaster, setShowMaster] = useState(false)
  const [isLoading, setIsLoading]   = useState(false)
  const [error, setError]           = useState<string | null>(null)

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!form.site_name || !form.username || !form.plaintext_password || !form.master_password) {
      setError('Please fill in all required fields.')
      return
    }

    setIsLoading(true)
    try {
      await vaultApi.create({
        site_name: form.site_name,
        username: form.username,
        plaintext_password: form.plaintext_password,
        master_password: form.master_password,
        label: form.label || undefined,
      })
      onCreated()
      onClose()
    } catch (err: any) {
      const detail = err?.response?.data?.detail ?? ''
      if (err?.response?.status === 503) {
        setError('Share nodes are not available. Start the share node services first.')
      } else if (detail.includes('encryption_salt')) {
        setError('User account missing encryption salt. Please re-register.')
      } else {
        setError(detail || 'Failed to create vault entry.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Fix 1 — block backdrop close while submitting */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={isLoading ? undefined : onClose} />
      <div className="relative w-full max-w-md bg-card border border-border rounded-xl shadow-2xl animate-fade-in">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <div>
            <h2 className="font-display font-bold text-base">New vault entry</h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Encrypted with AES-256-GCM · Split into 4 Shamir shares
            </p>
          </div>
          <button
            onClick={isLoading ? undefined : onClose}
            className="text-muted-foreground hover:text-foreground transition-colors disabled:opacity-40"
            disabled={isLoading}
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2.5 text-xs text-destructive animate-fade-in">
              <AlertCircle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="site_name">Site name <span className="text-destructive">*</span></Label>
              <div className="relative">
                <Globe className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
                <Input id="site_name" placeholder="github.com" value={form.site_name} onChange={set('site_name')} className="pl-8 h-8 text-sm" disabled={isLoading} />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="label">Label <span className="text-muted-foreground text-[10px]">(optional)</span></Label>
              <div className="relative">
                <Tag className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
                <Input id="label" placeholder="Work account" value={form.label} onChange={set('label')} className="pl-8 h-8 text-sm" disabled={isLoading} />
              </div>
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="username">Username / Email <span className="text-destructive">*</span></Label>
            <div className="relative">
              <User className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
              <Input id="username" placeholder="you@example.com" value={form.username} onChange={set('username')} className="pl-8 h-8 text-sm" disabled={isLoading} />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="plaintext_password">Password <span className="text-destructive">*</span></Label>
            <div className="relative">
              <Lock className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
              <Input
                id="plaintext_password"
                type={showPass ? 'text' : 'password'}
                placeholder="••••••••"
                value={form.plaintext_password}
                onChange={set('plaintext_password')}
                className="pl-8 pr-8 h-8 text-sm"
                disabled={isLoading}
              />
              <button type="button" onClick={() => setShowPass(!showPass)} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground" tabIndex={-1}>
                {showPass ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>

          {/* Divider */}
          <div className="relative py-1">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border" />
            </div>
            <div className="relative flex justify-center">
              <span className="bg-card px-3 text-[10px] text-muted-foreground font-mono uppercase tracking-wider">
                master password — never stored
              </span>
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="master_password">Master password <span className="text-destructive">*</span></Label>
            <div className="relative">
              <ShieldAlert className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-cyan-400/70" />
              <Input
                id="master_password"
                type={showMaster ? 'text' : 'password'}
                placeholder="Your vault master password"
                value={form.master_password}
                onChange={set('master_password')}
                className="pl-8 pr-8 h-8 text-sm border-cyan-500/20 focus-visible:ring-cyan-500/30"
                disabled={isLoading}
              />
              <button type="button" onClick={() => setShowMaster(!showMaster)} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground" tabIndex={-1}>
                {showMaster ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
              </button>
            </div>
            <p className="text-[10px] text-muted-foreground font-mono">
              Used to derive your AES-256 encryption key. Never transmitted or stored.
            </p>
          </div>

          <div className="flex gap-2 pt-2">
            <Button type="button" variant="outline" size="sm" className="flex-1" onClick={onClose} disabled={isLoading}>
              Cancel
            </Button>
            <Button type="submit" size="sm" className="flex-1" disabled={isLoading}>
              {isLoading ? (
                <span className="flex items-center gap-1.5">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Encrypting...
                </span>
              ) : 'Save to vault'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── Retrieve Modal ────────────────────────────────────────────────────────────

interface RetrieveModalProps {
  entry: VaultEntryMeta
  onClose: () => void
}

function RetrieveModal({ entry, onClose }: RetrieveModalProps) {
  const [masterPassword, setMasterPassword] = useState('')
  const [showMaster, setShowMaster] = useState(false)
  const [isLoading, setIsLoading]   = useState(false)
  const [error, setError]           = useState<string | null>(null)
  const [plaintext, setPlaintext]   = useState<string | null>(null)
  const [showPlain, setShowPlain]   = useState(false)
  const [copied, setCopied]         = useState(false)

  const handleRetrieve = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!masterPassword) { setError('Master password required.'); return }
    setError(null)
    setIsLoading(true)
    try {
      const res = await vaultApi.retrieve(entry.id, masterPassword)
      setPlaintext(res.plaintext_password)
    } catch (err: any) {
      const status = err?.response?.status
      if (status === 503) {
        setError('Share nodes unavailable. Start share node services to retrieve passwords.')
      } else if (status === 401) {
        setError('Wrong master password or data was tampered with.')
      } else if (status === 404) {
        setError('Vault entry not found.')
      } else {
        setError(err?.response?.data?.detail ?? 'Retrieval failed.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleCopy = () => {
    if (!plaintext) return
    navigator.clipboard.writeText(plaintext)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Fix 2 — block backdrop close while reconstructing or showing plaintext */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={isLoading ? undefined : onClose} />
      <div className="relative w-full max-w-sm bg-card border border-border rounded-xl shadow-2xl animate-fade-in">

        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <div>
            <h2 className="font-display font-bold text-sm">{entry.site_name}</h2>
            <p className="text-xs text-muted-foreground font-mono">{entry.username}</p>
          </div>
          <button
            onClick={isLoading ? undefined : onClose}
            className="text-muted-foreground hover:text-foreground disabled:opacity-40"
            disabled={isLoading}
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-5 space-y-4">
          {!plaintext ? (
            <form onSubmit={handleRetrieve} className="space-y-4">
              <p className="text-xs text-muted-foreground">
                Enter your master password to reconstruct this secret from Shamir shares.
              </p>

              {error && (
                <div className="flex items-start gap-2 rounded border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive">
                  <AlertCircle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                  {error}
                </div>
              )}

              <div className="space-y-1.5">
                <Label htmlFor="mp">Master password</Label>
                <div className="relative">
                  <Lock className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
                  <Input
                    id="mp"
                    type={showMaster ? 'text' : 'password'}
                    placeholder="••••••••"
                    value={masterPassword}
                    onChange={e => setMasterPassword(e.target.value)}
                    className="pl-8 pr-8 h-8 text-sm"
                    disabled={isLoading}
                    autoFocus
                  />
                  <button type="button" onClick={() => setShowMaster(!showMaster)} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground" tabIndex={-1}>
                    {showMaster ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              <div className="flex gap-2">
                <Button type="button" variant="outline" size="sm" className="flex-1" onClick={onClose} disabled={isLoading}>Cancel</Button>
                <Button type="submit" size="sm" className="flex-1" disabled={isLoading}>
                  {isLoading ? (
                    <span className="flex items-center gap-1.5">
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      Reconstructing...
                    </span>
                  ) : 'Retrieve'}
                </Button>
              </div>
            </form>
          ) : (
            <div className="space-y-4">
              <p className="text-xs text-emerald-400 font-mono">✓ Reconstructed from Shamir shares</p>
              <div className="space-y-1.5">
                <Label>Password</Label>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Input
                      type={showPlain ? 'text' : 'password'}
                      value={plaintext}
                      readOnly
                      className="pr-8 h-8 text-sm font-mono bg-secondary/50"
                    />
                    <button type="button" onClick={() => setShowPlain(!showPlain)} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground" tabIndex={-1}>
                      {showPlain ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                  <Button type="button" variant="outline" size="icon" className="h-8 w-8 shrink-0" onClick={handleCopy}>
                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </Button>
                </div>
                <p className="text-[10px] text-muted-foreground font-mono">
                  Not stored anywhere. Close this dialog to discard.
                </p>
              </div>
              <Button variant="outline" size="sm" className="w-full" onClick={onClose}>Done</Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Delete Confirm ────────────────────────────────────────────────────────────

interface DeleteConfirmProps {
  entry: VaultEntryMeta
  onClose: () => void
  onDeleted: () => void
}

function DeleteConfirm({ entry, onClose, onDeleted }: DeleteConfirmProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError]         = useState<string | null>(null)

  const handleDelete = async () => {
    setIsLoading(true)
    try {
      await vaultApi.delete(entry.id)
      onDeleted()
      onClose()
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? 'Delete failed.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Fix 3 — block backdrop close while deleting */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={isLoading ? undefined : onClose} />
      <div className="relative w-full max-w-sm bg-card border border-border rounded-xl shadow-2xl animate-fade-in p-6 space-y-4">
        <div className="space-y-1">
          <h2 className="font-display font-bold text-base">Delete vault entry?</h2>
          <p className="text-sm text-muted-foreground">
            This will permanently delete <span className="text-foreground font-medium">{entry.site_name}</span> and all its Shamir shares from every node. This cannot be undone.
          </p>
        </div>

        {error && (
          <div className="flex items-start gap-2 rounded border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive">
            <AlertCircle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
            {error}
          </div>
        )}

        <div className="flex gap-2">
          <Button variant="outline" size="sm" className="flex-1" onClick={onClose} disabled={isLoading}>Cancel</Button>
          <Button variant="destructive" size="sm" className="flex-1" onClick={handleDelete} disabled={isLoading}>
            {isLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : 'Delete'}
          </Button>
        </div>
      </div>
    </div>
  )
}

// ── Vault Entry Card ──────────────────────────────────────────────────────────

interface EntryCardProps {
  entry: VaultEntryMeta
  onRetrieve: (e: VaultEntryMeta) => void
  onDelete:   (e: VaultEntryMeta) => void
}

function EntryCard({ entry, onRetrieve, onDelete }: EntryCardProps) {
  return (
    <div className="glass rounded-lg p-4 flex items-center gap-4 group hover:border-border/80 transition-all duration-150 animate-fade-in">
      <div className="w-9 h-9 rounded-lg bg-secondary border border-border flex items-center justify-center shrink-0 font-mono text-xs font-bold text-muted-foreground">
        {getInitials(entry.site_name)}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="font-medium text-sm truncate">{entry.site_name}</p>
          {entry.label && (
            <Badge variant="secondary" className="text-[10px] shrink-0">{entry.label}</Badge>
          )}
        </div>
        <p className="text-xs text-muted-foreground font-mono truncate">{entry.username}</p>
      </div>
      <p className="text-xs text-muted-foreground font-mono shrink-0 hidden sm:block">
        {timeAgo(entry.created_at)}
      </p>
      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 text-muted-foreground hover:text-cyan-400"
          onClick={() => onRetrieve(entry)}
          title="Retrieve password"
        >
          <Eye className="w-3.5 h-3.5" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 text-muted-foreground hover:text-destructive"
          onClick={() => onDelete(entry)}
          title="Delete entry"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </Button>
      </div>
    </div>
  )
}

// ── Main VaultPage ────────────────────────────────────────────────────────────

export default function VaultPage() {
  const [entries, setEntries]             = useState<VaultEntryMeta[]>([])
  const [total, setTotal]                 = useState(0)
  const [isLoading, setIsLoading]         = useState(true)
  const [error, setError]                 = useState<string | null>(null)
  const [search, setSearch]               = useState('')
  const [showCreate, setShowCreate]       = useState(false)
  const [retrieveEntry, setRetrieveEntry] = useState<VaultEntryMeta | null>(null)
  const [deleteEntry, setDeleteEntry]     = useState<VaultEntryMeta | null>(null)
  const [nodeDown, setNodeDown]           = useState(false)

  const fetchEntries = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await vaultApi.list()
      setEntries(res.data)
      setTotal(res.total)
    } catch (err: any) {
      if (err?.response?.status === 503) {
        setNodeDown(true)
      } else {
        setError(err?.response?.data?.detail ?? 'Failed to load vault entries.')
      }
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => { fetchEntries() }, [fetchEntries])

  const filtered = entries.filter(e =>
    e.site_name.toLowerCase().includes(search.toLowerCase()) ||
    e.username.toLowerCase().includes(search.toLowerCase()) ||
    (e.label ?? '').toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6 page-enter">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold">Vault</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {total} {total === 1 ? 'entry' : 'entries'} · AES-256-GCM encrypted · N=4 Shamir shares
          </p>
        </div>
        <Button size="sm" className="gap-2" onClick={() => setShowCreate(true)}>
          <Plus className="w-4 h-4" />
          <span className="hidden sm:inline">Add entry</span>
        </Button>
      </div>

      {nodeDown && <NodeUnavailableBanner />}

      {entries.length > 0 && (
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search by site, username or label..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
      )}

      {error && (
        <div className="flex items-start gap-3 rounded-md border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
          {error}
        </div>
      )}

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-16 rounded-lg shimmer" />
          ))}
        </div>
      ) : entries.length === 0 ? (
        <EmptyState onAdd={() => setShowCreate(true)} />
      ) : filtered.length === 0 ? (
        <div className="text-center py-12 text-sm text-muted-foreground">
          No entries match <span className="font-mono text-foreground">"{search}"</span>
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map(entry => (
            <EntryCard
              key={entry.id}
              entry={entry}
              onRetrieve={setRetrieveEntry}
              onDelete={setDeleteEntry}
            />
          ))}
        </div>
      )}

      {showCreate && (
        <CreateModal
          onClose={() => setShowCreate(false)}
          onCreated={fetchEntries}
        />
      )}
      {retrieveEntry && (
        <RetrieveModal
          entry={retrieveEntry}
          onClose={() => setRetrieveEntry(null)}
        />
      )}
      {deleteEntry && (
        <DeleteConfirm
          entry={deleteEntry}
          onClose={() => setDeleteEntry(null)}
          onDeleted={fetchEntries}
        />
      )}
    </div>
  )
}