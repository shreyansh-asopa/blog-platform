import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { useSearchParams } from 'react-router'
import { postsApi } from '../api/endpoints'
import type { TopicDetail } from '../api/types'
import { useTopics } from '../api/useTopics'
import { Icon } from '../components/Icon'
import { PostList } from '../components/PostList'
import { TopicDot } from '../components/TopicTags'
import { plural } from '../lib/format'
import { searchParams, topicsIn } from '../lib/search'
import styles from './SearchPage.module.css'

const PAGE_SIZE = 10

// "Travel, Food & Cooking or Books & Reading"
const anyOf = new Intl.ListFormat('en-GB', { type: 'disjunction' })

/** /search?q=…&topic=…&topic=…: published posts, best match first, in any of the topics */
export function SearchPage() {
  const [params, setParams] = useSearchParams()
  const q = (params.get('q') ?? '').trim()
  const selected = topicsIn(params)
  const page = Math.max(1, Number(params.get('page')) || 1)
  const topics = useTopics()
  const names = (topics.data ?? []).filter((t) => selected.includes(t.slug)).map((t) => t.name)

  const results = useQuery({
    queryKey: ['posts', 'search', q, selected, page],
    queryFn: () => postsApi.feed(page, PAGE_SIZE, { q, topics: selected }),
    // Topics on their own list their posts, newest first
    enabled: q !== '' || selected.length > 0,
    placeholderData: keepPreviousData,
  })

  const where = names.length ? ` in ${anyOf.format(names)}` : ''
  // A string, so the effect below runs only when the title really changes
  const what = q ? `${q}${where}` : anyOf.format(names)
  useEffect(() => {
    document.title = what ? `${what} · Search · Lumen` : 'Search · Lumen'
    return () => {
      document.title = 'Lumen'
    }
  }, [what])

  const href = (n: number) => `?${searchParams(q, selected, n)}`

  return (
    <div className={styles.page}>
      <h1 className={styles.heading}>Search</h1>

      {/* key: Back and Forward change ?q without a submit, and a new key gives a fresh
          box showing the URL's search */}
      <SearchForm
        key={q}
        initial={q}
        // A new search is a new history entry, so Back returns to the previous one
        onSearch={(next) => setParams(searchParams(next, selected))}
      />

      {topics.data && (
        <TopicFilter
          topics={topics.data}
          selected={selected}
          // Changing the topics keeps the words, and starts again from page 1
          onSelect={(next) => setParams(searchParams(q, next))}
        />
      )}

      {q === '' && selected.length === 0 ? (
        <div className={`muted ${styles.tips}`}>
          <p>
            Searches the titles and text of every published post. Pick topics above to narrow it
            down, or to browse them. You can use:
          </p>
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
              {q
                ? `${plural(results.data.total, 'result')} for “${q}”${where}`
                : `${plural(results.data.total, 'post')}${where}`}
            </p>
          )}
          <PostList
            posts={results}
            page={page}
            size={PAGE_SIZE}
            href={href}
            empty={
              <>
                <p>{q ? `No posts match “${q}”${where}.` : `No posts${where} yet.`}</p>
                <p className="muted">
                  {selected.length
                    ? 'Try other topics, or all topics.'
                    : 'Try fewer or different words.'}
                </p>
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

interface FilterProps {
  topics: TopicDetail[]
  /** Topic slugs; none means all topics */
  selected: string[]
  onSelect: (slugs: string[]) => void
}

/** A row of topic toggles under the search box. Pick any number; "All" clears them. */
function TopicFilter({ topics, selected, onSelect }: FilterProps) {
  return (
    <div className={styles.filter} role="group" aria-label="Filter by topic">
      <button className="chip" aria-pressed={selected.length === 0} onClick={() => onSelect([])}>
        All topics
      </button>
      {topics.map((topic) => {
        const on = selected.includes(topic.slug)
        return (
          <button
            key={topic.slug}
            className="chip"
            aria-pressed={on}
            onClick={() =>
              onSelect(on ? selected.filter((s) => s !== topic.slug) : [...selected, topic.slug])
            }
          >
            <TopicDot slug={topic.slug} />
            {topic.name}
          </button>
        )
      })}
    </div>
  )
}
