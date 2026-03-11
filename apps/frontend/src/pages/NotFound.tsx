import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-6 page-enter">
      <p className="font-mono text-xs text-muted-foreground tracking-widest uppercase">404</p>
      <h1 className="text-4xl font-display font-bold text-foreground">Page not found</h1>
      <p className="text-muted-foreground text-sm">This shard doesn't exist.</p>
      <Button asChild variant="outline" size="sm">
        <Link to="/dashboard">Back to vault</Link>
      </Button>
    </div>
  )
}