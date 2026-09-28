import { lazy, Suspense } from 'react'
import { RequireAuth } from '../auth/RequireAuth'

// The editor brings a large rich-text library, so it loads only when someone starts writing
const EditorPage = lazy(() =>
  import('./EditorPage').then((module) => ({ default: module.EditorPage })),
)

/** /write and /edit/:slug: logged-in only, and fetched on first visit */
export function EditorRoute() {
  return (
    <RequireAuth>
      <Suspense fallback={<p className="muted">Loading editor…</p>}>
        <EditorPage />
      </Suspense>
    </RequireAuth>
  )
}
