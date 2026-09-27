import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'
import { postsApi } from '../api/endpoints'
import { formatDate, plural } from '../lib/format'
import { ErrorMessage } from './ErrorMessage'
import { Icon } from './Icon'
import { TopicDot } from './TopicTags'
import styles from './TrendingPosts.module.css'

const LIMIT = 5

/** The posts with the most likes and comments this week, as a numbered list */
export function TrendingPosts() {
  const trending = useQuery({
    // Under 'posts', so a like or comment anywhere refreshes the ranking too
    queryKey: ['posts', 'trending', LIMIT],
    queryFn: () => postsApi.trending(LIMIT),
  })

  if (trending.data?.length === 0) return null

  return (
    <section className={`card ${styles.trending}`} aria-labelledby="trending-title">
      <header className={styles.header}>
        <h2 id="trending-title">Trending posts</h2>
        <span className="muted">Most liked and discussed this week</span>
      </header>

      {trending.isPending && <p className="muted">Loading trending posts…</p>}
      {trending.isError && <ErrorMessage error={trending.error} />}

      <ol className={styles.list}>
        {trending.data?.map((post, i) => (
          <li key={post.id} className={styles.item}>
            <span className={styles.rank} aria-hidden>
              {String(i + 1).padStart(2, '0')}
            </span>
            <div className={styles.body}>
              <h3 className={styles.title}>
                {/* Stretched over the whole row, like the post cards */}
                <Link to={`/p/${post.slug}`} className={styles.link}>
                  {post.title}
                </Link>
              </h3>
              <p className={`muted ${styles.meta}`}>
                <Link to={`/u/${post.author.username}`} className={styles.author}>
                  {post.author.username}
                </Link>
                <span aria-hidden>·</span>
                <time dateTime={post.published_at ?? post.updated_at}>
                  {formatDate(post.published_at ?? post.updated_at)}
                </time>
              </p>
              <p className={`muted ${styles.stats}`}>
                {post.topics[0] && (
                  <span className={styles.topic}>
                    <TopicDot slug={post.topics[0].slug} />
                    {post.topics[0].name}
                  </span>
                )}
                <span aria-label={plural(post.like_count, 'like')}>
                  <Icon name="heart" size={14} /> {post.like_count}
                </span>
                <span aria-label={plural(post.comment_count, 'comment')}>
                  <Icon name="comment" size={14} /> {post.comment_count}
                </span>
              </p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  )
}
