import { Link } from 'react-router'
import type { Topic } from '../api/types'
import styles from './TopicTags.module.css'

// The glow colour of each topic's artwork (backend/scripts/draw_sample_art.py)
const COLORS: Record<string, string> = {
  ai: '#a78bfa',
  genai: '#fb7185',
  'machine-learning': '#2dd4bf',
  'data-engineering': '#34d399',
  'software-engineering': '#60a5fa',
  'cloud-devops': '#38bdf8',
  'web-development': '#fbbf24',
  security: '#4ade80',
  lifestyle: '#fb923c',
  travel: '#818cf8',
  food: '#ef4444',
  'health-wellness': '#f472b6',
  'personal-finance': '#eab308',
  books: '#e879f9',
}

/** A coloured dot that marks a topic in lists */
export function TopicDot({ slug }: { slug: string }) {
  return (
    <span
      className={styles.dot}
      style={{ background: COLORS[slug] ?? 'var(--accent)' }}
      aria-hidden
    />
  )
}

/** A post's topics, each linking to its topic page */
export function TopicTags({ topics, className = '' }: { topics: Topic[]; className?: string }) {
  if (topics.length === 0) return null
  return (
    <ul className={`${styles.tags} ${className}`} aria-label="Topics">
      {topics.map((topic) => (
        <li key={topic.slug}>
          <Link to={`/t/${topic.slug}`} className="chip">
            <TopicDot slug={topic.slug} />
            {topic.name}
          </Link>
        </li>
      ))}
    </ul>
  )
}
