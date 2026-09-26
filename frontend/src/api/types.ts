// Mirrors of the backend's Pydantic schemas (backend/app/schemas). Dates arrive as ISO strings.

export type Role = 'user' | 'admin'

export interface User {
  id: string
  email: string
  username: string
  role: Role
  is_active: boolean
  created_at: string
}

export interface Token {
  access_token: string
  token_type: 'bearer'
}

export interface Page<T> {
  items: T[]
  total: number
  page: number
  size: number
}

export interface Author {
  id: string
  username: string
}

export type PostStatus = 'draft' | 'published'

/** What you send to create or edit a post */
export interface PostInput {
  title: string
  content: string
}

export interface PostSummary {
  id: string
  title: string
  slug: string
  excerpt: string
  status: PostStatus
  cover_image: string | null
  published_at: string | null
  created_at: string
  updated_at: string
  author: Author
  like_count: number
  comment_count: number
}

/** A post as its author gets it back after saving */
export interface PostRead extends PostSummary {
  content: string
}

export interface PostDetail extends PostRead {
  /** Always false when logged out */
  liked_by_me: boolean
}

export interface LikeStatus {
  post_id: string
  liked: boolean
  like_count: number
}

export interface Comment {
  id: string
  post_id: string
  content: string
  created_at: string
  updated_at: string
  author: Author
}
