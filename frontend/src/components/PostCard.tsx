import type { PostSummary } from '../api/types'
import { Avatar } from './Avatar'
import styles from './PostCard.module.css'

const dateFormat = new Intl.DateTimeFormat(undefined, {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
})

export function PostCard({ post }: { post: PostSummary }) {
  const date = post.published_at ?? post.updated_at

  return (
    <article className={`card ${styles.card}`}>
      <header className={styles.meta}>
        <Avatar name={post.author.username} size={28} />
        <div>
          <div className={styles.author}>{post.author.username}</div>
          <time className="muted" dateTime={date}>
            {dateFormat.format(new Date(date))}
          </time>
        </div>
      </header>

      <h2 className={styles.title}>{post.title}</h2>
      {post.excerpt && <p className={`muted ${styles.excerpt}`}>{post.excerpt}</p>}

      <footer className={`muted ${styles.stats}`}>
        <span aria-label={`${post.like_count} likes`}>♥ {post.like_count}</span>
        <span aria-label={`${post.comment_count} comments`}>💬 {post.comment_count}</span>
      </footer>
    </article>
  )
}
