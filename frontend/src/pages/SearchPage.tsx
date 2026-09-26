import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { useSearchParams } from 'react-router'
import { postsApi } from '../api/endpoints'
import { Icon } from '../components/Icon'
import { PostList } from '../components/PostList'
import { plural } from '../lib/format'
import styles from './SearchPage.module.css'

const PAGE_SIZE = 10

/** /search?q=…: published posts, best match first */
export function SearchPage() {
  const [params, setParams] = useSearchParams()
  const q = (params.get('q') ?? '').trim()
  const page = Math.max(1, Number(params.get('page')) || 1)

  const results = useQuery({
    queryKey: ['posts', 'search', q, page],
    queryFn: () => postsApi.feed(page, PAGE_SIZE, { q }),
    enabled: q !== '',
    placeholderData: keepPreviousData,
  })

  useEffect(() => {
    document.title = q ? `${q} · Search · Lumen` : 'Search · Lumen'
    return () => {
      document.title = 'Lumen'
    }
  }, [q])

  const href = (n: number) => `?${new URLSearchParams(n === 1 ? { q } : { q, page: String(n) })}`

  return (
    <div className={styles.page}>
      <h1 className={styles.heading}>Search</h1>

      {/* key: Back and Forward change ?q without a submit, and a new key gives a fresh
          box showing the URL's search */}
      <SearchForm
        key={q}
        initial={q}
        // A new search is a new history entry, so Back returns to the previous one
        onSearch={(next) => setParams(next ? { q: next } : {})}
      />

      {q === '' ? (
        <div className={`muted ${styles.tips}`}>
          <p>Searches the titles and text of every published post. You can use:</p>
          <ul>
            <li>
              <code>"exact phrase"</code> for words next to each other
            </li>
            <li>
              <code>react or vue</code> for either word
            </li>
            <li>
              <code>python -django</code> to leave a word out
            </li>
          </ul>
        </div>
      ) : (
        <>
          {results.data && (
            <p className="muted" aria-live="polite">
              {plural(results.data.total, 'result')} for “{q}”
            </p>
          )}
          <PostList
            posts={results}
            page={page}
            size={PAGE_SIZE}
            href={href}
            empty={
              <>
                <p>No posts match “{q}”.</p>
                <p className="muted">Try fewer or different words.</p>
              </>
            }
          />
        </>
      )}
    </div>
  )
}

function SearchForm({ initial, onSearch }: { initial: string; onSearch: (q: string) => void }) {
  // What's in the box; the URL only changes on submit
  const [typed, setTyped] = useState(initial)

  function submit(event: FormEvent) {
    event.preventDefault()
    onSearch(typed.trim())
  }

  return (
    <form role="search" className={styles.form} onSubmit={submit}>
      <label htmlFor="search-box" className="visually-hidden">
        Search posts
      </label>
      <Icon name="search" />
      <input
        id="search-box"
        type="search"
        className={styles.input}
        placeholder="Search posts…"
        value={typed}
        onChange={(event) => setTyped(event.target.value)}
        maxLength={200}
        autoFocus
      />
      <button type="submit" className="btn btn-primary">
        Search
      </button>
    </form>
  )
}
