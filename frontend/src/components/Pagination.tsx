import { Link } from 'react-router'
import styles from './Pagination.module.css'

interface Props {
  page: number
  size: number
  total: number
  /** Builds the link for a page number, e.g. (n) => `/?page=${n}` */
  href: (page: number) => string
}

/** Previous / next links. Pages live in the URL, so they can be shared and survive a reload */
export function Pagination({ page, size, total, href }: Props) {
  const pages = Math.max(1, Math.ceil(total / size))
  if (pages === 1) return null

  return (
    <nav className={styles.pagination} aria-label="Pagination">
      {page > 1 ? (
        <Link className="btn btn-outline" to={href(page - 1)} rel="prev">
          ← Newer
        </Link>
      ) : (
        <span />
      )}
      <span className="muted">
        Page {page} of {pages}
      </span>
      {page < pages ? (
        <Link className="btn btn-outline" to={href(page + 1)} rel="next">
          Older →
        </Link>
      ) : (
        <span />
      )}
    </nav>
  )
}
