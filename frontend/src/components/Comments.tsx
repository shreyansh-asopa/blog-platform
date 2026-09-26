import { useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { Link, useLocation } from 'react-router'
import { commentsApi } from '../api/endpoints'
import type { Comment, PostDetail, User } from '../api/types'
import { useAuth } from '../auth/useAuth'
import { formatDate, plural } from '../lib/format'
import { Avatar } from './Avatar'
import styles from './Comments.module.css'
import { ErrorMessage } from './ErrorMessage'

const PAGE_SIZE = 20

// Mirrors the backend rule: the comment's author, the post's author, and admins
function canDelete(user: User | null, comment: Comment, post: PostDetail): boolean {
  if (!user) return false
  return user.role === 'admin' || user.id === comment.author.id || user.id === post.author.id
}

export function Comments({ post }: { post: PostDetail }) {
  const { user } = useAuth()
  const location = useLocation()
  const queryClient = useQueryClient()
  const key = ['comments', post.id]

  // Oldest first, a page at a time, with a "Show more" button for the rest
  const comments = useInfiniteQuery({
    queryKey: key,
    queryFn: ({ pageParam }) => commentsApi.list(post.id, pageParam, PAGE_SIZE),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.page * last.size < last.total ? last.page + 1 : undefined),
  })

  // After adding or deleting: reload the comments, and the post and feed for their counts
  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: key })
    queryClient.invalidateQueries({ queryKey: ['post', post.slug] })
    queryClient.invalidateQueries({ queryKey: ['posts'] })
  }

  const [draft, setDraft] = useState('')
  const add = useMutation({
    mutationFn: (content: string) => commentsApi.create(post.id, content),
    onSuccess: () => {
      setDraft('')
      refresh()
    },
  })

  const remove = useMutation({ mutationFn: commentsApi.remove, onSuccess: refresh })

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (draft.trim()) add.mutate(draft)
  }

  function handleDelete(comment: Comment) {
    if (window.confirm('Delete this comment?')) remove.mutate(comment.id)
  }

  const items = comments.data?.pages.flatMap((page) => page.items) ?? []
  const total = comments.data?.pages[0]?.total ?? post.comment_count

  return (
    <section className={`card ${styles.section}`} aria-labelledby="comments-heading">
      <h2 id="comments-heading" className={styles.heading}>
        {plural(total, 'comment')}
      </h2>

      {user ? (
        <form className={styles.form} onSubmit={handleSubmit}>
          <Avatar name={user.username} />
          <div className={styles.formBody}>
            <label htmlFor="new-comment" className="visually-hidden">
              Add a comment
            </label>
            <textarea
              id="new-comment"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="Add to the discussion"
              maxLength={5000}
              rows={3}
            />
            {/* e.g. moderation rejected it, or too many comments in a minute */}
            {add.isError && <ErrorMessage error={add.error} />}
            <button className="btn btn-primary" disabled={add.isPending || !draft.trim()}>
              {add.isPending ? 'Posting…' : 'Comment'}
            </button>
          </div>
        </form>
      ) : (
        <p className="muted">
          <Link to="/login" state={{ from: location.pathname }} className={styles.loginLink}>
            Log in
          </Link>{' '}
          to join the discussion.
        </p>
      )}

      {comments.isError && <ErrorMessage error={comments.error} />}
      {remove.isError && <ErrorMessage error={remove.error} />}

      <ol className={styles.list}>
        {items.map((comment) => (
          <li key={comment.id} className={styles.comment}>
            <Avatar name={comment.author.username} size={28} />
            <div className={styles.body}>
              <div className={styles.meta}>
                <strong>{comment.author.username}</strong>
                {comment.author.id === post.author.id && (
                  <span className={styles.badge}>Author</span>
                )}
                <time className="muted" dateTime={comment.created_at}>
                  {formatDate(comment.created_at)}
                </time>
                {canDelete(user, comment, post) && (
                  <button
                    className={`btn btn-ghost ${styles.delete}`}
                    onClick={() => handleDelete(comment)}
                    disabled={remove.isPending}
                  >
                    Delete
                  </button>
                )}
              </div>
              {/* Plain text, not Markdown: React escapes it, and line breaks are kept by CSS */}
              <p className={styles.text}>{comment.content}</p>
            </div>
          </li>
        ))}
      </ol>

      {comments.hasNextPage && (
        <button
          className="btn btn-outline"
          onClick={() => comments.fetchNextPage()}
          disabled={comments.isFetchingNextPage}
        >
          {comments.isFetchingNextPage ? 'Loading…' : 'Show more comments'}
        </button>
      )}
    </section>
  )
}
