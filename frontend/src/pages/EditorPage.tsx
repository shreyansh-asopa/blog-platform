import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useDeferredValue, useEffect, useRef, useState } from 'react'
import type { KeyboardEvent } from 'react'
import { Link, useBlocker, useLocation, useNavigate, useParams } from 'react-router'
import type { NavigateOptions } from 'react-router'
import { ApiError } from '../api/client'
import { postsApi } from '../api/endpoints'
import type { PostDetail, PostRead } from '../api/types'
import { useAiInfo } from '../api/useAiInfo'
import { useTopics } from '../api/useTopics'
import { useAuth } from '../auth/useAuth'
import { AiPanel } from '../components/AiPanel'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { ErrorMessage } from '../components/ErrorMessage'
import { Icon } from '../components/Icon'
import { Markdown } from '../components/Markdown'
import { TopicDot } from '../components/TopicTags'
import { NotFoundPage } from './PlaceholderPage'
import styles from './EditorPage.module.css'

// The same limits the backend enforces (backend/app/schemas/post.py, core/config.py)
const TITLE_MAX = 200
const CONTENT_MAX = 100_000
const COVER_MAX_BYTES = 5 * 1024 * 1024
const COVER_TYPES = 'image/jpeg,image/png,image/webp'
const TOPICS_MAX = 3

const slugsOf = (post: PostRead) => post.topics.map((t) => t.slug)
/** Same topics, in any order */
const sameTopics = (a: string[], b: string[]) =>
  a.length === b.length && a.every((slug) => b.includes(slug))

interface EditorState {
  /** Keeps the same editor on screen when saving changes the URL (see EditorPage) */
  editorKey?: string
}

/** /write starts a new post; /edit/:slug loads one of yours */
export function EditorPage() {
  const { slug } = useParams()
  const { user } = useAuth()
  const location = useLocation()
  const post = useQuery({
    queryKey: ['post', slug],
    queryFn: () => postsApi.bySlug(slug!),
    enabled: slug !== undefined,
  })

  // The key decides when React throws the editor away and starts a fresh one:
  // - "Write" in the sidebar gets a new location.key each click, so a blank editor
  // - saving a new post moves /write to /edit/:slug, and passes its key along in the
  //   navigation state, so what you typed stays put
  const key = (location.state as EditorState | null)?.editorKey ?? post.data?.id ?? location.key

  if (slug === undefined) return <Editor key={key} editorKey={key} />
  if (post.isPending) return <p className="muted">Loading…</p>
  if (post.error instanceof ApiError && post.error.status === 404) return <NotFoundPage />
  if (post.isError) return <ErrorMessage error={post.error} />

  // Anyone can read a published post, but only its author (or an admin) may edit it
  if (post.data.author.id !== user?.id && user?.role !== 'admin') {
    return <ErrorMessage error={new Error('You can only edit your own posts.')} />
  }
  return <Editor key={key} editorKey={key} initial={post.data} />
}

type Action = 'save' | 'publish' | 'unpublish'

function Editor({ editorKey, initial }: { editorKey: string; initial?: PostRead }) {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const contentRef = useRef<HTMLTextAreaElement>(null)

  // `saved` is the post as the server last confirmed it; title, content and topics are the form
  const [saved, setSaved] = useState<PostRead | null>(initial ?? null)
  const [title, setTitle] = useState(initial?.title ?? '')
  const [content, setContent] = useState(initial?.content ?? '')
  const [topics, setTopics] = useState<string[]>(initial ? slugsOf(initial) : [])
  const [notice, setNotice] = useState('')
  // Beside the text: its preview, or the AI assistant
  const [side, setSide] = useState<'preview' | 'ai'>('preview')
  // On narrow screens only one pane fits, so you switch between the text and the side
  const [view, setView] = useState<'write' | 'side'>('write')
  const ai = useAiInfo()
  const aiOn = ai.data !== undefined && ai.data.status !== 'off'
  const show = (pane: 'preview' | 'ai') => {
    setSide(pane)
    setView('side')
  }

  // Rendering Markdown on every keystroke can lag on long posts. A deferred value lets
  // React update the textarea first and catch the preview up a moment later.
  const preview = useDeferredValue(content)

  const dirty = saved
    ? title.trim() !== saved.title ||
      content !== saved.content ||
      !sameTopics(topics, slugsOf(saved))
    : title !== '' || content !== '' || topics.length > 0
  const complete = title.trim() !== '' && content.trim() !== ''
  const published = saved?.status === 'published'

  useEffect(() => {
    document.title = `${saved ? 'Edit' : 'Write'} · Lumen`
    return () => {
      document.title = 'Lumen'
    }
  }, [saved])

  // Closing the tab or reloading with unsaved work makes the browser ask first
  useEffect(() => {
    if (!dirty) return
    const warn = (event: BeforeUnloadEvent) => event.preventDefault()
    window.addEventListener('beforeunload', warn)
    return () => window.removeEventListener('beforeunload', warn)
  }, [dirty])

  // Any other move inside Lumen (a link, the Back button, even "Write" again, which starts a
  // blank editor) asks with our own dialog. The editor's own moves, like /write becoming
  // /edit/:slug after a save, set `ours` so they go through: they run before React
  // re-renders, while `dirty` still reads true.
  const ours = useRef(false)
  const blocker = useBlocker(() => dirty && !ours.current)

  function go(to: string, options?: NavigateOptions) {
    ours.current = true
    navigate(to, options)
    ours.current = false
  }

  /** Takes in a post the server just returned: the editor, the cache and the URL follow it */
  function remember(post: PostRead, previous: PostRead | null) {
    setSaved(post)
    queryClient.setQueryData<PostDetail>(['post', post.slug], (old) => ({
      ...post,
      liked_by_me: old?.liked_by_me ?? false,
    }))
    queryClient.invalidateQueries({ queryKey: ['posts'] })
    // Topic post counts change as posts are published or refiled
    queryClient.invalidateQueries({ queryKey: ['topics'] })
    queryClient.invalidateQueries({ queryKey: ['topic'] })
    // A new post gets its first URL, and a draft's URL follows its title
    if (post.slug !== previous?.slug) {
      go(`/edit/${post.slug}`, { replace: true, state: { editorKey } })
    }
  }

  const change = useMutation({
    mutationFn: async (action: Action) => {
      let post = saved
      // Save first, so publishing never loses the latest edits. Each step is remembered
      // straight away: if publishing then fails, a retry won't create a second copy.
      if (!post || dirty) {
        const data = { title, content, topics }
        const next = post ? await postsApi.update(post.id, data) : await postsApi.create(data)
        remember(next, post)
        post = next
      }
      if (action === 'publish') post = await postsApi.publish(post.id)
      if (action === 'unpublish') post = await postsApi.unpublish(post.id)
      return post
    },
    onSuccess: (post, action) => {
      remember(post, post)
      if (action === 'publish') go(`/p/${post.slug}`)
      else if (action === 'unpublish') setNotice('Moved back to drafts')
      else setNotice(published ? 'Changes saved' : 'Draft saved')
    },
    onError: () => setNotice(''),
  })

  const cover = useMutation({
    mutationFn: (file: File | null) => {
      if (!saved) throw new Error('Save the post first')
      if (!file) return postsApi.removeCover(saved.id)
      // Checked here too, so a big photo fails at once instead of after a slow upload
      if (file.size > COVER_MAX_BYTES) {
        throw new ApiError(413, 'file_too_large', 'The cover must be at most 5 MB.')
      }
      return postsApi.uploadCover(saved.id, file)
    },
    onSuccess: (post) => {
      remember(post, saved)
      setNotice(post.cover_image ? 'Cover updated' : 'Cover removed')
    },
  })

  const busy = change.isPending || cover.isPending
  const run = (action: Action) => {
    if (complete && !busy) change.mutate(action)
  }

  // Ctrl+S (⌘S on a Mac) saves instead of opening the browser's "Save page" dialog
  function onKeyDown(event: KeyboardEvent) {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 's') {
      event.preventDefault()
      run('save')
    }
  }

  const status = change.isPending
    ? 'Saving…'
    : cover.isPending
      ? 'Uploading cover…'
      : dirty
        ? 'Unsaved changes'
        : notice

  return (
    <div className={styles.page} onKeyDown={onKeyDown}>
      <header className={styles.toolbar}>
        <div className={styles.state}>
          <span className={styles.badge} data-status={saved?.status ?? 'new'}>
            {published ? 'Published' : saved ? 'Draft' : 'New post'}
          </span>
          <span className="muted" role="status">
            {status}
          </span>
        </div>

        <div className={styles.actions}>
          {aiOn && (
            <button
              className={`btn btn-ghost ${styles.aiButton}`}
              aria-pressed={side === 'ai'}
              onClick={() => (side === 'ai' ? setSide('preview') : show('ai'))}
            >
              <Icon name="sparkles" size={16} /> AI assistant
            </button>
          )}
          {published && (
            <>
              <Link to={`/p/${saved.slug}`} className="btn btn-ghost">
                View
              </Link>
              <button className="btn btn-ghost" onClick={() => run('unpublish')} disabled={busy}>
                Unpublish
              </button>
            </>
          )}
          <button
            className="btn btn-outline"
            onClick={() => run('save')}
            disabled={!complete || busy || (saved !== null && !dirty)}
          >
            {published ? 'Save changes' : 'Save draft'}
          </button>
          {!published && (
            <button
              className="btn btn-primary"
              onClick={() => run('publish')}
              disabled={!complete || busy}
            >
              Publish
            </button>
          )}
        </div>
      </header>

      {blocker.state === 'blocked' && (
        <ConfirmDialog
          title="Leave without saving?"
          confirmLabel="Discard changes"
          cancelLabel="Keep editing"
          onConfirm={() => blocker.proceed()}
          onCancel={() => blocker.reset()}
        >
          <p>Your unsaved changes to this post will be lost.</p>
        </ConfirmDialog>
      )}

      {change.isError && <ErrorMessage error={change.error} />}
      {cover.isError && <ErrorMessage error={cover.error} />}

      <CoverPicker
        image={saved?.cover_image ?? null}
        needsSave={!saved}
        disabled={!saved || busy}
        onPick={(file) => cover.mutate(file)}
        onRemove={() => cover.mutate(null)}
      />

      <label className="visually-hidden" htmlFor="post-title">
        Title
      </label>
      <input
        id="post-title"
        className={styles.title}
        value={title}
        onChange={(event) => setTitle(event.target.value)}
        // Enter moves on to the body, as in most editors, instead of doing nothing
        onKeyDown={(event) => {
          if (event.key === 'Enter') {
            event.preventDefault()
            contentRef.current?.focus()
          }
        }}
        placeholder="Post title…"
        maxLength={TITLE_MAX}
        autoFocus={!initial}
      />

      <TopicPicker selected={topics} onChange={setTopics} disabled={busy} />

      <div className={styles.tabs}>
        <button
          className={styles.tab}
          aria-pressed={view === 'write'}
          onClick={() => setView('write')}
        >
          <Icon name="pen" size={16} /> Write
        </button>
        <button
          className={styles.tab}
          aria-pressed={view === 'side' && side === 'preview'}
          onClick={() => show('preview')}
        >
          <Icon name="posts" size={16} /> Preview
        </button>
        {aiOn && (
          <button
            className={styles.tab}
            aria-pressed={view === 'side' && side === 'ai'}
            onClick={() => show('ai')}
          >
            <Icon name="sparkles" size={16} /> AI
          </button>
        )}
      </div>

      <div className={styles.panes} data-view={view}>
        <div className={styles.writePane}>
          <label className="visually-hidden" htmlFor="post-content">
            Content, in Markdown
          </label>
          <textarea
            id="post-content"
            ref={contentRef}
            className={styles.content}
            value={content}
            onChange={(event) => setContent(event.target.value)}
            placeholder={
              'Write your post here…\n\nMarkdown works: ## headings, **bold**, `code`, lists, > quotes and more.'
            }
            maxLength={CONTENT_MAX}
            spellCheck
          />
          <p className={`muted ${styles.hint}`}>
            Markdown supported. <kbd>Ctrl</kbd>/<kbd>⌘</kbd> + <kbd>S</kbd> saves.
            {content.length > CONTENT_MAX * 0.9 &&
              ` ${(CONTENT_MAX - content.length).toLocaleString()} characters left.`}
          </p>
        </div>

        <section
          className={`card ${styles.previewPane}`}
          aria-label="Preview"
          hidden={side !== 'preview'}
        >
          {title.trim() || preview.trim() ? (
            <>
              <h1 className={styles.previewTitle}>{title || 'Untitled'}</h1>
              <Markdown>{preview}</Markdown>
            </>
          ) : (
            <p className="muted">Your preview appears here as you type.</p>
          )}
        </section>

        {/* Kept mounted while hidden, so switching to the preview doesn't lose an answer */}
        {aiOn && (
          <section
            className={`card ${styles.previewPane}`}
            aria-label="AI assistant"
            hidden={side !== 'ai'}
          >
            <AiPanel title={title} content={content} onChange={setContent} />
          </section>
        )}
      </div>
    </div>
  )
}

interface TopicPickerProps {
  selected: string[]
  onChange: (slugs: string[]) => void
  disabled: boolean
}

/** Toggles for filing the post under up to three topics. Saved with the post. */
function TopicPicker({ selected, onChange, disabled }: TopicPickerProps) {
  const topics = useTopics()
  if (!topics.data) return null
  const full = selected.length >= TOPICS_MAX

  return (
    <div className={styles.topics} role="group" aria-labelledby="topics-label">
      <span id="topics-label" className={`muted ${styles.topicsLabel}`}>
        Topics <span>(up to {TOPICS_MAX})</span>
      </span>
      {topics.data.map((topic) => {
        const on = selected.includes(topic.slug)
        return (
          <button
            key={topic.slug}
            type="button"
            className="chip"
            aria-pressed={on}
            // Once three are picked, the rest wait until one is taken off
            disabled={disabled || (full && !on)}
            onClick={() =>
              onChange(on ? selected.filter((s) => s !== topic.slug) : [...selected, topic.slug])
            }
          >
            <TopicDot slug={topic.slug} />
            {topic.name}
          </button>
        )
      })}
    </div>
  )
}

interface CoverProps {
  image: string | null
  /** A new post has no id yet, so there is nothing to attach a cover to */
  needsSave: boolean
  disabled: boolean
  onPick: (file: File) => void
  onRemove: () => void
}

/** Shows the cover, or a button to add one. Covers need a saved post to belong to. */
function CoverPicker({ image, needsSave, disabled, onPick, onRemove }: CoverProps) {
  const input = (
    <input
      type="file"
      accept={COVER_TYPES}
      className="visually-hidden"
      disabled={disabled}
      onChange={(event) => {
        const file = event.target.files?.[0]
        // Cleared, so picking the same file again still counts as a change
        event.target.value = ''
        if (file) onPick(file)
      }}
    />
  )

  if (image) {
    return (
      <div className={styles.cover}>
        <img src={image} alt="Cover" />
        <div className={styles.coverActions}>
          <label className="btn btn-ghost" aria-disabled={disabled}>
            Change {input}
          </label>
          <button className="btn btn-ghost" onClick={onRemove} disabled={disabled}>
            Remove
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.addCover}>
      <label className="btn btn-outline" aria-disabled={disabled}>
        Add a cover {input}
      </label>
      <span className="muted">
        {needsSave ? 'Save a draft first, then add a cover.' : 'JPEG, PNG or WebP, up to 5 MB.'}
      </span>
    </div>
  )
}
