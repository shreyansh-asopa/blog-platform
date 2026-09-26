import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useLocation, useNavigate } from 'react-router'
import { postsApi } from '../api/endpoints'
import type { PostDetail } from '../api/types'
import { useAuth } from '../auth/useAuth'
import { plural } from '../lib/format'
import styles from './LikeButton.module.css'

export function LikeButton({ post }: { post: PostDetail }) {
  const { user } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const queryClient = useQueryClient()
  const key = ['post', post.slug]

  const toggle = useMutation({
    mutationFn: (like: boolean) => (like ? postsApi.like(post.id) : postsApi.unlike(post.id)),
    // "Optimistic update": show the new heart and count at once, before the server answers
    onMutate: async (like) => {
      await queryClient.cancelQueries({ queryKey: key })
      const before = queryClient.getQueryData<PostDetail>(key)
      queryClient.setQueryData<PostDetail>(
        key,
        (p) => p && { ...p, liked_by_me: like, like_count: p.like_count + (like ? 1 : -1) },
      )
      return { before }
    },
    // If the request fails, put back what was there
    onError: (_error, _like, context) => queryClient.setQueryData(key, context?.before),
    // The server's answer is the truth (someone else may have liked it meanwhile)
    onSuccess: (status) =>
      queryClient.setQueryData<PostDetail>(
        key,
        (p) => p && { ...p, liked_by_me: status.liked, like_count: status.like_count },
      ),
    // The feed shows like counts too, so mark it out of date
    onSettled: () => queryClient.invalidateQueries({ queryKey: ['posts'] }),
  })

  function handleClick() {
    if (!user) {
      navigate('/login', { state: { from: location.pathname } })
      return
    }
    toggle.mutate(!post.liked_by_me)
  }

  return (
    <button
      className={`btn ${styles.like}`}
      onClick={handleClick}
      disabled={toggle.isPending}
      aria-pressed={post.liked_by_me}
      aria-label={`${post.liked_by_me ? 'Unlike' : 'Like'} (${plural(post.like_count, 'like')})`}
      title={user ? undefined : 'Log in to like posts'}
    >
      <span className={styles.heart} aria-hidden>
        {post.liked_by_me ? '♥' : '♡'}
      </span>
      {post.like_count}
    </button>
  )
}
