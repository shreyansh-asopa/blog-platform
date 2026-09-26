import { useQuery } from '@tanstack/react-query'
import { useEffect } from 'react'
import { Link, useParams } from 'react-router'
import { ApiError } from '../api/client'
import { postsApi } from '../api/endpoints'
import { useAuth } from '../auth/useAuth'
import { Avatar } from '../components/Avatar'
import { Comments } from '../components/Comments'
import { ErrorMessage } from '../components/ErrorMessage'
import { LikeButton } from '../components/LikeButton'
import { Markdown } from '../components/Markdown'
import { formatDate } from '../lib/format'
import { NotFoundPage } from './PlaceholderPage'
import styles from './PostPage.module.css'

export function PostPage() {
  const { slug = '' } = useParams()
  const { user } = useAuth()
  const post = useQuery({ queryKey: ['post', slug], queryFn: () => postsApi.bySlug(slug) })

  useEffect(() => {
    if (post.data) document.title = `${post.data.title} · Lumen`
    return () => {
      document.title = 'Lumen'
    }
  }, [post.data])

  if (post.isPending) return <p className="muted">Loading…</p>
  // Unknown slugs and other people's drafts both come back as 404
  if (post.error instanceof ApiError && post.error.status === 404) return <NotFoundPage />
  if (post.isError) return <ErrorMessage error={post.error} />

  const p = post.data
  const date = p.published_at ?? p.updated_at
  const canEdit = user !== null && (user.id === p.author.id || user.role === 'admin')

  return (
    <div className={styles.page}>
      <article className={`card ${styles.article}`}>
        {p.cover_image && <img className={styles.cover} src={p.cover_image} alt="" />}

        <div className={styles.inner}>
          {p.status === 'draft' && (
            <p className={styles.draft}>Draft: only you (and admins) can see this.</p>
          )}

          <header className={styles.meta}>
            <Avatar name={p.author.username} size={40} />
            <div>
              <div className={styles.author}>{p.author.username}</div>
              <time className="muted" dateTime={date}>
                {p.published_at ? `Posted ${formatDate(date)}` : `Edited ${formatDate(date)}`}
              </time>
            </div>
          </header>

          <h1 className={styles.title}>{p.title}</h1>

          <Markdown>{p.content}</Markdown>

          <footer className={styles.actions}>
            <LikeButton post={p} />
            {canEdit && (
              <Link to={`/edit/${p.slug}`} className="btn btn-ghost">
                Edit post
              </Link>
            )}
          </footer>
        </div>
      </article>

      {p.status === 'published' && <Comments post={p} />}
    </div>
  )
}
