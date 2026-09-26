import { api } from './client'
import type { Page, PostSummary, Token, User } from './types'

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
}
