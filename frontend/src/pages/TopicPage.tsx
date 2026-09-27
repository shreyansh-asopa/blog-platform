import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useEffect } from 'react'
import { Link, useParams, useSearchParams } from 'react-router'
import { ApiError } from '../api/client'
import { postsApi, topicsApi } from '../api/endpoints'
import { ErrorMessage } from '../components/ErrorMessage'
import { Icon } from '../components/Icon'
import { PostList } from '../components/PostList'
import { plural } from '../lib/format'
import { NotFoundPage } from './PlaceholderPage'
import styles from './TopicPage.module.css'

const PAGE_SIZE = 10

/** /t/:slug: a topic's banner and its published posts, newest first */
export function TopicPage() {
  const { slug = '' } = useParams()
  const [params] = useSearchParams()
  const page = Math.max(1, Number(params.get('page')) || 1)

  const topic = useQuery({ queryKey: ['topic', slug], queryFn: () => topicsApi.get(slug) })
  // Fetched alongside the topic, not after it, so the page appears in one step
  const posts = useQuery({
    queryKey: ['posts', 'topic', slug, page],
    queryFn: () => postsApi.feed(page, PAGE_SIZE, { topic: slug }),
    placeholderData: keepPreviousData,
  })

  useEffect(() => {
    if (topic.data) document.title = `${topic.data.name} · Lumen`
    return () => {
      document.title = 'Lumen'
    }
  }, [topic.data])

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [slug, page])

  if (topic.isPending) return <p className="muted">Loading…</p>
  if (topic.error instanceof ApiError && topic.error.status === 404) return <NotFoundPage />
  if (topic.isError) return <ErrorMessage error={topic.error} />

  const t = topic.data

  return (
    <div className={styles.page}>
      {/* The banner art is in public/topics, one per topic */}
      <header
        className={styles.banner}
        style={{ backgroundImage: `url(/topics/${encodeURIComponent(t.slug)}.webp)` }}
      >
        <p className={styles.kicker}>Topic</p>
        <h1 className={styles.name}>{t.name}</h1>
        <p className={styles.description}>{t.description}</p>
        <div className={styles.footer}>
          <span>{plural(t.post_count, 'post')}</span>
          <Link to={`/search?topic=${t.slug}`} className={`btn ${styles.searchLink}`}>
            <Icon name="search" size={16} /> Search in {t.name}
          </Link>
        </div>
      </header>

      <h2 className={styles.subheading}>Latest in {t.name}</h2>
      <PostList
        posts={posts}
        page={page}
        size={PAGE_SIZE}
        href={(n) => (n === 1 ? `/t/${t.slug}` : `/t/${t.slug}?page=${n}`)}
        empty={
          <>
            <p>No posts in {t.name} yet.</p>
            <p className="muted">Write one and pick this topic in the editor.</p>
          </>
        }
      />
    </div>
  )
}
