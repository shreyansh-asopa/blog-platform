import { Link } from 'react-router'
import type { PostSummary } from '../api/types'
import { formatDate, plural } from '../lib/format'
import { Avatar } from './Avatar'
import { Icon } from './Icon'
import styles from './PostCard.module.css'

export function PostCard({ post }: { post: PostSummary }) {
  const date = post.published_at ?? post.updated_at

  return (
    <article className={`card ${styles.card}`}>
      <header className={styles.meta}>
        <Avatar name={post.author.username} size={28} />
        <div>
          {/* Above the card-wide link, so it can be clicked on its own */}
          <Link to={`/u/${post.author.username}`} className={styles.author}>
            {post.author.username}
          </Link>
          <time className="muted" dateTime={date}>
            {formatDate(date)}
          </time>
        </div>
      </header>

      <h2 className={styles.title}>
        {/* The link's ::after stretches over the whole card, so any click opens the post */}
        <Link to={`/p/${post.slug}`} className={styles.link}>
          {post.title}
        </Link>
      </h2>
      {post.excerpt && <p className={`muted ${styles.excerpt}`}>{post.excerpt}</p>}

      <footer className={`muted ${styles.stats}`}>
        <span aria-label={plural(post.like_count, 'like')}>
          <Icon name="heart" size={16} /> {post.like_count}
        </span>
        <span aria-label={plural(post.comment_count, 'comment')}>
          <Icon name="comment" size={16} /> {post.comment_count}
        </span>
      </footer>
    </article>
  )
}
