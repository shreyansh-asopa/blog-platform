import { Link } from 'react-router'

/** Stands in for pages that later PRs build, so every sidebar link already goes somewhere */
export function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="card" style={{ padding: 32 }}>
      <h1 style={{ marginTop: 0 }}>{title}</h1>
      <p className="muted">This page is coming in the next few pull requests.</p>
    </div>
  )
}

export function NotFoundPage() {
  return (
    <div className="card" style={{ padding: 32, textAlign: 'center' }}>
      <h1 style={{ marginTop: 0 }}>Page not found</h1>
      <p className="muted">That page doesn't exist, or it has moved.</p>
      <Link to="/" className="btn btn-primary">
        Back to Home
      </Link>
    </div>
  )
}
