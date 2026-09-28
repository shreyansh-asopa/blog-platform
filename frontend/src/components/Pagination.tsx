import { Link } from 'react-router'
import { pageNumbers } from '../lib/pages'
import styles from './Pagination.module.css'

interface Props {
  page: number
  size: number
  total: number
  /** Builds the link for a page number, e.g. (n) => `/?page=${n}` */
  href: (page: number) => string
}

/** Previous / next links and page numbers. Pages live in the URL, so they can be shared and survive a reload */
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
      <ol className={styles.numbers}>
        {pageNumbers(page, pages).map((n, i) =>
          n === null ? (
            <li key={`gap-${i}`} className={styles.gap} aria-hidden>
              …
            </li>
          ) : (
            <li key={n}>
              <Link
                to={href(n)}
                className={n === page ? `${styles.number} ${styles.current}` : styles.number}
                aria-current={n === page ? 'page' : undefined}
                aria-label={`Page ${n}`}
              >
                {n}
              </Link>
            </li>
          ),
        )}
      </ol>
      {/* Phones have no room for every number */}
      <span className={`muted ${styles.summary}`}>
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
