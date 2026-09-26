import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useEffect } from 'react'
import { useParams, useSearchParams } from 'react-router'
import { ApiError } from '../api/client'
import { postsApi, usersApi } from '../api/endpoints'
import { Avatar } from '../components/Avatar'
import { ErrorMessage } from '../components/ErrorMessage'
import { PostList } from '../components/PostList'
import { formatDate, plural } from '../lib/format'
import { NotFoundPage } from './PlaceholderPage'
import styles from './AuthorPage.module.css'

const PAGE_SIZE = 10

/** /u/:username: an author's profile and their published posts, newest first */
export function AuthorPage() {
  const { username = '' } = useParams()
  const [params] = useSearchParams()
  const page = Math.max(1, Number(params.get('page')) || 1)

  const profile = useQuery({
    queryKey: ['profile', username],
    queryFn: () => usersApi.profile(username),
  })
  // Fetched alongside the profile, not after it, so the page appears in one step
  const posts = useQuery({
    queryKey: ['posts', 'author', username, page],
    queryFn: () => postsApi.feed(page, PAGE_SIZE, { author: username }),
    placeholderData: keepPreviousData,
  })

  useEffect(() => {
    document.title = `${username} · Lumen`
    return () => {
      document.title = 'Lumen'
    }
  }, [username])

  if (profile.isPending) return <p className="muted">Loading…</p>
  if (profile.error instanceof ApiError && profile.error.status === 404) return <NotFoundPage />
  if (profile.isError) return <ErrorMessage error={profile.error} />

  const { data: author } = profile

  return (
    <div className={styles.page}>
      <header className={`card ${styles.profile}`}>
        <Avatar name={author.username} size={72} />
        <div>
          <h1 className={styles.name}>{author.username}</h1>
          <p className="muted">
            Joined {formatDate(author.created_at)} · {plural(author.post_count, 'post')}
          </p>
        </div>
      </header>

      <h2 className={styles.subheading}>Posts</h2>
      <PostList
        posts={posts}
        page={page}
        size={PAGE_SIZE}
        href={(n) => (n === 1 ? `/u/${username}` : `/u/${username}?page=${n}`)}
        empty={<p className="muted">{author.username} hasn't published anything yet.</p>}
      />
    </div>
  )
}
