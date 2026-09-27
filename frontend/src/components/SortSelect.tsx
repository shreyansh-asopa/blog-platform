import type { Sort } from '../api/types'
import { Icon } from './Icon'
import styles from './SortSelect.module.css'

interface Props {
  value: Sort
  onChange: (sort: Sort) => void
  /** What the dates are, for screen readers: "published" on the feed, "edited" on your own posts */
  by?: string
}

/** A compact "Newest first / Oldest first" dropdown, placed beside a search bar */
export function SortSelect({ value, onChange, by = 'published' }: Props) {
  return (
    <label className={styles.sort}>
      <span className="visually-hidden">Sort posts by date {by}</span>
      <Icon name="sort" size={16} />
      <select value={value} onChange={(event) => onChange(event.target.value as Sort)}>
        <option value="newest">Newest first</option>
        <option value="oldest">Oldest first</option>
      </select>
    </label>
  )
}
