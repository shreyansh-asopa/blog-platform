import { api, download } from './client'
import type {
  AuditAction,
  AuditLog,
  Comment,
  LikeStatus,
  Page,
  PostDetail,
  PostInput,
  PostRead,
  PostStatus,
  PostSummary,
  Profile,
  Role,
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
  /** `q` searches (best match first); `author` is a username */
  feed: (page = 1, size = 20, filters: { q?: string; author?: string } = {}) =>
    api<Page<PostSummary>>(`/posts${query({ page, size, ...filters })}`),
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

/** Builds "?a=1&b=2", leaving out empty values */
function query(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') search.set(key, String(value))
  }
  return `?${search}`
}

export const usersApi = {
  profile: (username: string) => api<Profile>(`/users/${encodeURIComponent(username)}`),
}

export const adminApi = {
  users: (page = 1, size = 20, search?: string, role?: Role) =>
    api<Page<User>>(`/admin/users${query({ page, size, search, role })}`),
  setRole: (userId: string, role: Role) =>
    api<User>(`/admin/users/${userId}/role`, { method: 'PATCH', body: { role } }),
  auditLogs: (page = 1, size = 20, action?: AuditAction) =>
    api<Page<AuditLog>>(`/admin/audit-logs${query({ page, size, action })}`),
}
