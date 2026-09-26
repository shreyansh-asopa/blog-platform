import type { UseQueryResult } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import type { Page, PostSummary } from '../api/types'
import { ErrorMessage } from './ErrorMessage'
import { Pagination } from './Pagination'
import { PostCard } from './PostCard'
import styles from './PostList.module.css'

interface Props {
  posts: UseQueryResult<Page<PostSummary>>
  page: number
  size: number
  href: (page: number) => string
  /** Shown when there is nothing to list */
  empty: ReactNode
}

/** A page of post cards, with its loading, error and empty states and the page links */
export function PostList({ posts, page, size, href, empty }: Props) {
  if (posts.isPending) return <p className="muted">Loading posts…</p>
  if (posts.isError) return <ErrorMessage error={posts.error} />

  return (
    <>
      {posts.data.items.length === 0 ? (
        <div className={`card ${styles.empty}`}>
          {page > 1 ? <p>No posts on this page.</p> : empty}
        </div>
      ) : (
        <div className={styles.list} aria-busy={posts.isPlaceholderData}>
          {posts.data.items.map((post) => (
            <PostCard key={post.id} post={post} />
          ))}
        </div>
      )}
      <Pagination page={page} size={size} total={posts.data.total} href={href} />
    </>
  )
}
