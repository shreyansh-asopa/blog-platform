import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect } from 'react'
import { Link, NavLink, useSearchParams } from 'react-router'
import { meApi, postsApi } from '../api/endpoints'
import type { ExportFormat, PostStatus, PostSummary, Sort } from '../api/types'
import { ErrorMessage } from '../components/ErrorMessage'
import { Icon } from '../components/Icon'
import { Pagination } from '../components/Pagination'
import { SearchForm } from '../components/SearchForm'
import { SortSelect } from '../components/SortSelect'
import { formatDate, plural } from '../lib/format'
import styles from './MyPostsPage.module.css'

const PAGE_SIZE = 10

const TABS: { label: string; to: string; pathname: string; status?: PostStatus }[] = [
  { label: 'All', to: '/me/posts', pathname: '/me/posts' },
  {
    label: 'Published',
    to: '/me/posts?status=published',
    pathname: '/me/posts',
    status: 'published',
  },
  { label: 'Drafts', to: '/me/drafts', pathname: '/me/drafts', status: 'draft' },
]

const EXPORTS: { format: ExportFormat; label: string; title: string }[] = [
  { format: 'pdf', label: 'PDF', title: 'Download these posts as a PDF document' },
  { format: 'docx', label: 'Word', title: 'Download these posts as a Word document' },
]

/** Your posts, newest edit first, searchable. /me/drafts is the same page, filtered to drafts. */
export function MyPostsPage({ drafts = false }: { drafts?: boolean }) {
  const [params, setParams] = useSearchParams()
  const page = Math.max(1, Number(params.get('page')) || 1)
  const q = (params.get('q') ?? '').trim()
  const sort: Sort = params.get('sort') === 'oldest' ? 'oldest' : 'newest'
  const status: PostStatus | undefined = drafts
    ? 'draft'
    : params.get('status') === 'published'
      ? 'published'
      : undefined
  const tab = TABS.find((t) => t.status === status) ?? TABS[0]

  const posts = useQuery({
    queryKey: ['posts', 'mine', status ?? 'all', q, sort, page],
    queryFn: () => meApi.posts(page, PAGE_SIZE, status, q || undefined, sort),
    placeholderData: keepPreviousData,
  })
  // The download holds the same posts as the list: this tab, and the search if there is one
  const exportFile = useMutation({
    mutationFn: (format: ExportFormat) => meApi.export(format, status, q || undefined),
  })

  useEffect(() => {
    document.title = `${drafts ? 'Drafts' : 'My posts'} · Lumen`
    return () => {
      document.title = 'Lumen'
    }
  }, [drafts])

  /** The URL query for this tab with a search, sort and page, leaving out the defaults */
  function filters(nextQ: string, nextSort: Sort, n = 1) {
    const query = new URLSearchParams(tab.to.split('?')[1])
    if (nextQ) query.set('q', nextQ)
    if (nextSort === 'oldest') query.set('sort', nextSort)
    if (n > 1) query.set('page', String(n))
    return query
  }

  // Page links keep the current filters, e.g. /me/posts?status=published&q=lisbon&page=2
  const href = (n: number) => {
    const query = filters(q, sort, n)
    return query.size ? `${tab.pathname}?${query}` : tab.pathname
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div>
          <h1>{drafts ? 'Drafts' : 'My posts'}</h1>
          {posts.data && <p className="muted">{plural(posts.data.total, 'post')}</p>}
        </div>
        <div className={styles.headerActions}>
          {EXPORTS.map(({ format, label, title }) => (
            <button
              key={format}
              className="btn btn-outline"
              onClick={() => exportFile.mutate(format)}
              disabled={exportFile.isPending || posts.data?.total === 0}
              title={title}
            >
              <Icon name="download" size={16} />
              {exportFile.isPending && exportFile.variables === format ? 'Preparing…' : label}
            </button>
          ))}
          <Link to="/write" className="btn btn-primary">
            <Icon name="pen" size={16} /> Write
          </Link>
        </div>
      </header>

      <nav className={styles.tabs} aria-label="Filter posts">
        {TABS.map((t) => (
          // NavLink ignores ?query when matching, so the active tab is chosen here instead
          <NavLink
            key={t.label}
            to={t.to}
            end
            className={t === tab ? `${styles.tab} ${styles.active}` : styles.tab}
            aria-current={t === tab ? 'page' : undefined}
          >
            {t.label}
          </NavLink>
        ))}
      </nav>

      <div className={styles.toolbar}>
        {/* key: a new ?q (Back, Forward, a tab) gives a fresh box showing it */}
        <SearchForm
          key={q}
          id="my-posts-search"
          initial={q}
          placeholder="Search your own stories…"
          onSearch={(next) => setParams(filters(next, sort))}
        />
        <SortSelect value={sort} by="edited" onChange={(next) => setParams(filters(q, next))} />
      </div>

      {exportFile.isError && <ErrorMessage error={exportFile.error} />}
      {posts.isPending && <p className="muted">Loading your posts…</p>}
      {posts.isError && <ErrorMessage error={posts.error} />}

      {posts.data?.items.length === 0 && (
        <div className={`card ${styles.empty}`}>
          <p>
            {page > 1
              ? 'No posts on this page.'
              : q
                ? `None of your posts match "${q}".`
                : status === 'draft'
                  ? 'No drafts. Everything you have started is published.'
                  : status === 'published'
                    ? 'Nothing published yet.'
                    : 'You have not written anything yet.'}
          </p>
          <Link to="/write" className="btn btn-primary">
            Write a post
          </Link>
        </div>
      )}

      <ul className={styles.list} aria-busy={posts.isPlaceholderData}>
        {posts.data?.items.map((post) => (
          <PostRow key={post.id} post={post} />
        ))}
      </ul>

      {posts.data && (
        <Pagination page={page} size={PAGE_SIZE} total={posts.data.total} href={href} />
      )}
    </div>
  )
}

type RowAction = 'publish' | 'unpublish' | 'delete'

function PostRow({ post }: { post: PostSummary }) {
  const queryClient = useQueryClient()
  const published = post.status === 'published'

  const act = useMutation({
    // The rows only need to know it worked; the lists are refetched below
    mutationFn: async (action: RowAction) => {
      if (action === 'delete') await postsApi.remove(post.id)
      else if (action === 'publish') await postsApi.publish(post.id)
      else await postsApi.unpublish(post.id)
    },
    onSuccess: () => {
      // The row may move to another tab or vanish, so every post list refetches
      queryClient.invalidateQueries({ queryKey: ['posts'] })
      queryClient.invalidateQueries({ queryKey: ['post', post.slug] })
    },
  })

  function remove() {
    if (window.confirm(`Delete "${post.title}"? This can't be undone from Lumen.`)) {
      act.mutate('delete')
    }
  }

  return (
    <li className={`card ${styles.row}`}>
      <div className={styles.rowMain}>
        <Link to={published ? `/p/${post.slug}` : `/edit/${post.slug}`} className={styles.title}>
          {post.title}
        </Link>
        <div className={`muted ${styles.meta}`}>
          <span className={styles.badge} data-status={post.status}>
            {published ? 'Published' : 'Draft'}
          </span>
          <span>
            {published && post.published_at
              ? `Published ${formatDate(post.published_at)}`
              : `Edited ${formatDate(post.updated_at)}`}
          </span>
          {published && (
            <>
              <span className={styles.stat}>
                <Icon name="heart" size={14} /> {post.like_count}
              </span>
              <span className={styles.stat}>
                <Icon name="comment" size={14} /> {post.comment_count}
              </span>
            </>
          )}
        </div>
        {act.isError && <ErrorMessage error={act.error} />}
      </div>

      <div className={styles.rowActions}>
        <Link to={`/edit/${post.slug}`} className="btn btn-ghost">
          Edit
        </Link>
        <button
          className="btn btn-ghost"
          onClick={() => act.mutate(published ? 'unpublish' : 'publish')}
          disabled={act.isPending}
        >
          {published ? 'Unpublish' : 'Publish'}
        </button>
        <button
          className={`btn btn-ghost ${styles.danger}`}
          onClick={remove}
          disabled={act.isPending}
        >
          Delete
        </button>
      </div>
    </li>
  )
}
