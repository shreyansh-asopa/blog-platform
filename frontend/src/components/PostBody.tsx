import type { PostRead } from '../api/types'
import { cleanHtml } from '../lib/html'
import { Markdown } from './Markdown'
import styles from './Markdown.module.css'

/** A post's text: rich-text posts are cleaned HTML, older ones Markdown */
export function PostBody({ post }: { post: Pick<PostRead, 'content' | 'content_format'> }) {
  if (post.content_format === 'markdown') return <Markdown>{post.content}</Markdown>
  return (
    <div className={styles.prose} dangerouslySetInnerHTML={{ __html: cleanHtml(post.content) }} />
  )
}
