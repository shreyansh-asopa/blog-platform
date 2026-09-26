import { useQuery } from '@tanstack/react-query'
import { postsApi } from '../api/endpoints'
import { ErrorMessage } from '../components/ErrorMessage'
import { PostCard } from '../components/PostCard'
import styles from './HomePage.module.css'

export function HomePage() {
  // Pagination and links to each post arrive with the reading pages in the next PR
  const feed = useQuery({ queryKey: ['posts', 'feed', 1], queryFn: () => postsApi.feed() })

  return (
    <section className={styles.feed}>
      <h1 className="visually-hidden">Latest posts</h1>
      {feed.isPending && <p className="muted">Loading posts…</p>}
      {feed.isError && <ErrorMessage error={feed.error} />}
      {feed.data?.items.length === 0 && (
        <div className={`card ${styles.empty}`}>
          <p>No posts yet. Be the first to write one!</p>
        </div>
      )}
      {feed.data?.items.map((post) => (
        <PostCard key={post.id} post={post} />
      ))}
    </section>
  )
}
