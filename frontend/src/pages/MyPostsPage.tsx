import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect } from 'react'
import { Link, NavLink, useSearchParams } from 'react-router'
import { meApi, postsApi } from '../api/endpoints'
import type { PostStatus, PostSummary } from '../api/types'
import { ErrorMessage } from '../components/ErrorMessage'
import { Icon } from '../components/Icon'
import { Pagination } from '../components/Pagination'
import { formatDate, plural } from '../lib/format'
import styles from './MyPostsPage.module.css'

const PAGE_SIZE = 10

const TABS: { label: string; to: string; status?: PostStatus }[] = [
  { label: 'All', to: '/me/posts' },
  { label: 'Published', to: '/me/posts?status=published', status: 'published' },
  { label: 'Drafts', to: '/me/drafts', status: 'draft' },
]

/** Your posts, newest edit first. /me/drafts is the same page, filtered to drafts. */
export function MyPostsPage({ drafts = false }: { drafts?: boolean }) {
  const [params] = useSearchParams()
  const page = Math.max(1, Number(params.get('page')) || 1)
  const status: PostStatus | undefined = drafts
    ? 'draft'
    : params.get('status') === 'published'
      ? 'published'
      : undefined
  const tab = TABS.find((t) => t.status === status) ?? TABS[0]

  const posts = useQuery({
    queryKey: ['posts', 'mine', status ?? 'all', page],
    queryFn: () => meApi.posts(page, PAGE_SIZE, status),
    placeholderData: keepPreviousData,
  })
  const exportCsv = useMutation({ mutationFn: () => meApi.exportCsv(status) })

  useEffect(() => {
    document.title = `${drafts ? 'Drafts' : 'My posts'} · Lumen`
    return () => {
      document.title = 'Lumen'
    }
  }, [drafts])

  // Page links keep the current filter, e.g. /me/posts?status=published&page=2
  const href = (n: number) => {
    const sep = tab.to.includes('?') ? '&' : '?'
    return n === 1 ? tab.to : `${tab.to}${sep}page=${n}`
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div>
          <h1>{drafts ? 'Drafts' : 'My posts'}</h1>
          {posts.data && <p className="muted">{plural(posts.data.total, 'post')}</p>}
        </div>
        <div className={styles.headerActions}>
          <button
            className="btn btn-outline"
            onClick={() => exportCsv.mutate()}
            disabled={exportCsv.isPending || posts.data?.total === 0}
            title="Download these posts as a spreadsheet file"
          >
            <Icon name="download" size={16} />
            {exportCsv.isPending ? 'Preparing…' : 'Export CSV'}
          </button>
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

      {exportCsv.isError && <ErrorMessage error={exportCsv.error} />}
      {posts.isPending && <p className="muted">Loading your posts…</p>}
      {posts.isError && <ErrorMessage error={posts.error} />}

      {posts.data?.items.length === 0 && (
        <div className={`card ${styles.empty}`}>
          <p>
            {page > 1
              ? 'No posts on this page.'
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
