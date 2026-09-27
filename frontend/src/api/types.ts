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

/** GET /users/{username}: what anyone can see about an author */
export interface Profile {
  id: string
  username: string
  created_at: string
  /** Published posts only */
  post_count: number
}

export interface Author {
  id: string
  username: string
}

export type PostStatus = 'draft' | 'published'

/** A subject posts are filed under. The list is fixed; see GET /topics */
export interface Topic {
  slug: string
  name: string
}

export interface TopicDetail extends Topic {
  description: string
  /** Published posts only */
  post_count: number
}

/** What you send to create or edit a post */
export interface PostInput {
  title: string
  content: string
  /** Topic slugs, at most three */
  topics: string[]
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
  topics: Topic[]
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

export type AuditAction =
  | 'user.role_changed'
  | 'post.updated'
  | 'post.published'
  | 'post.unpublished'
  | 'post.deleted'
  | 'comment.deleted'

/** One entry in the admin audit log: who did what, and when */
export interface AuditLog {
  id: number
  /** Null once the user who acted has been deleted */
  actor: Author | null
  action: AuditAction
  entity_type: string
  entity_id: string
  /** Depends on the action, e.g. {username, from, to} for a role change */
  details: Record<string, unknown>
  created_at: string
}

/** Whether the editor's AI help can answer, or what's missing */
export type AiStatus = 'ready' | 'off' | 'not_running' | 'model_missing' | 'no_key'

export interface AiInfo {
  status: AiStatus
  /** "claude" sends posts to Anthropic's API; "ollama" runs a model on Lumen's server */
  provider: 'claude' | 'ollama' | 'off'
  /** e.g. "claude-sonnet-5" or "llama3.1:8b" */
  model: string
  /** Longer posts are refused */
  max_chars: number
}

export type AiWriteAction = 'polish' | 'ideas' | 'recommend'

export interface GrammarFix {
  /** Exact words from the post */
  original: string
  fix: string
  reason: string
}
