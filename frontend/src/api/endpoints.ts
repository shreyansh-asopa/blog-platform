import { api } from './client'
import type { Comment, LikeStatus, Page, PostDetail, PostSummary, Token, User } from './types'

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
}

export const commentsApi = {
  list: (postId: string, page = 1, size = 20) =>
    api<Page<Comment>>(`/posts/${postId}/comments?page=${page}&size=${size}`),
  create: (postId: string, content: string) =>
    api<Comment>(`/posts/${postId}/comments`, { method: 'POST', body: { content } }),
  remove: (commentId: string) => api<void>(`/comments/${commentId}`, { method: 'DELETE' }),
}
