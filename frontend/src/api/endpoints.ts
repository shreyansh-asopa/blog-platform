import { api, download } from './client'
import type {
  Comment,
  LikeStatus,
  Page,
  PostDetail,
  PostInput,
  PostRead,
  PostStatus,
  PostSummary,
  Token,
  User,
} from './types'

export const authApi = {
  // The login endpoint is a standard OAuth2 password form, not JSON
  login: (username: string, password: string) =>
    api<Token>('/auth/login', {
      method: 'POST',
      body: new URLSearchParams({ username, password }),
    }),
  register: (data: { email: string; username: string; password: string }) =>
    api<User>('/auth/register', { method: 'POST', body: data }),
  me: () => api<User>('/users/me'),
}

export const postsApi = {
  feed: (page = 1, size = 20) => api<Page<PostSummary>>(`/posts?page=${page}&size=${size}`),
  bySlug: (slug: string) => api<PostDetail>(`/posts/${encodeURIComponent(slug)}`),
  like: (postId: string) => api<LikeStatus>(`/posts/${postId}/like`, { method: 'PUT' }),
  unlike: (postId: string) => api<LikeStatus>(`/posts/${postId}/like`, { method: 'DELETE' }),

  // Writing. New posts start as drafts; publishing is a separate step
  create: (data: PostInput) => api<PostRead>('/posts', { method: 'POST', body: data }),
  update: (postId: string, data: Partial<PostInput>) =>
    api<PostRead>(`/posts/${postId}`, { method: 'PATCH', body: data }),
  remove: (postId: string) => api<void>(`/posts/${postId}`, { method: 'DELETE' }),
  publish: (postId: string) => api<PostRead>(`/posts/${postId}/publish`, { method: 'POST' }),
  unpublish: (postId: string) => api<PostRead>(`/posts/${postId}/unpublish`, { method: 'POST' }),
  uploadCover: (postId: string, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api<PostRead>(`/posts/${postId}/cover`, { method: 'POST', body: form })
  },
  removeCover: (postId: string) => api<PostRead>(`/posts/${postId}/cover`, { method: 'DELETE' }),
}

export const meApi = {
  /** Your own posts, drafts included, most recently edited first */
  posts: (page = 1, size = 20, status?: PostStatus) =>
    api<Page<PostSummary>>(
      `/me/posts?page=${page}&size=${size}${status ? `&status=${status}` : ''}`,
    ),
  exportCsv: (status?: PostStatus) =>
    download(`/me/posts/export?format=csv${status ? `&status=${status}` : ''}`, 'lumen-posts.csv'),
}

export const commentsApi = {
  list: (postId: string, page = 1, size = 20) =>
    api<Page<Comment>>(`/posts/${postId}/comments?page=${page}&size=${size}`),
  create: (postId: string, content: string) =>
    api<Comment>(`/posts/${postId}/comments`, { method: 'POST', body: { content } }),
  remove: (commentId: string) => api<void>(`/comments/${commentId}`, { method: 'DELETE' }),
}
