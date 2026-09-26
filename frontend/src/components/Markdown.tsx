import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import styles from './Markdown.module.css'

/**
 * Renders a post's Markdown. Raw HTML inside the Markdown is shown as plain text, never run,
 * and react-markdown drops dangerous link targets like javascript: — so a post can't inject
 * scripts into its readers' pages.
 */
export function Markdown({ children }: { children: string }) {
  return (
    <div className={styles.prose}>
      <ReactMarkdown
        // Tables, ~~strikethrough~~, task lists and bare URLs, as on GitHub
        remarkPlugins={[remarkGfm]}
        components={{
          // Links to other sites open in a new tab; noopener stops them controlling this one
          a: ({ href, children }) => {
            const external = href?.startsWith('http')
            return (
              <a href={href} {...(external && { target: '_blank', rel: 'noopener noreferrer' })}>
                {children}
              </a>
            )
          },
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  )
}
