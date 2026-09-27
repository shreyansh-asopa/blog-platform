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
import styles from './SearchPage.module.css'

const PAGE_SIZE = 10

/** Builds the search URL's query, leaving out what's empty (and page 1) */
function searchParams(q: string, topic: string, page = 1) {
  const params: Record<string, string> = {}
  if (q) params.q = q
  if (topic) params.topic = topic
  if (page > 1) params.page = String(page)
  return params
}

/** /search?q=…&topic=…: published posts, best match first, optionally in one topic */
export function SearchPage() {
  const [params, setParams] = useSearchParams()
  const q = (params.get('q') ?? '').trim()
  const topic = (params.get('topic') ?? '').trim().toLowerCase()
  const page = Math.max(1, Number(params.get('page')) || 1)
  const topics = useTopics()
  const current = topics.data?.find((t) => t.slug === topic)

  const results = useQuery({
    queryKey: ['posts', 'search', q, topic, page],
    queryFn: () => postsApi.feed(page, PAGE_SIZE, { q, topic }),
    // A topic on its own lists that topic's posts, newest first
    enabled: q !== '' || topic !== '',
    placeholderData: keepPreviousData,
  })

  useEffect(() => {
    const what = [q, current?.name].filter(Boolean).join(' in ')
    document.title = what ? `${what} · Search · Lumen` : 'Search · Lumen'
    return () => {
      document.title = 'Lumen'
    }
  }, [q, current])

  const href = (n: number) => `?${new URLSearchParams(searchParams(q, topic, n))}`
  const where = current ? ` in ${current.name}` : ''

  return (
    <div className={styles.page}>
      <h1 className={styles.heading}>Search</h1>

      {/* key: Back and Forward change ?q without a submit, and a new key gives a fresh
          box showing the URL's search */}
      <SearchForm
        key={q}
        initial={q}
        // A new search is a new history entry, so Back returns to the previous one
        onSearch={(next) => setParams(searchParams(next, topic))}
      />

      {topics.data && (
        <TopicFilter
          topics={topics.data}
          selected={topic}
          // Picking a topic keeps the words, and starts again from page 1
          onSelect={(next) => setParams(searchParams(q, next))}
        />
      )}

      {q === '' && topic === '' ? (
        <div className={`muted ${styles.tips}`}>
          <p>
            Searches the titles and text of every published post. Pick a topic above to narrow it
            down, or to browse it. You can use:
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
                  {topic ? 'Try another topic, or all topics.' : 'Try fewer or different words.'}
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
  /** A topic slug, or '' for all topics */
  selected: string
  onSelect: (slug: string) => void
}

/** A row of topic toggles under the search box. One topic at a time; "All" clears it. */
function TopicFilter({ topics, selected, onSelect }: FilterProps) {
  return (
    <div className={styles.filter} role="group" aria-label="Filter by topic">
      <button className="chip" aria-pressed={selected === ''} onClick={() => onSelect('')}>
        All topics
      </button>
      {topics.map((topic) => (
        <button
          key={topic.slug}
          className="chip"
          aria-pressed={selected === topic.slug}
          // Clicking the chosen topic again turns the filter off
          onClick={() => onSelect(selected === topic.slug ? '' : topic.slug)}
        >
          <TopicDot slug={topic.slug} />
          {topic.name}
        </button>
      ))}
    </div>
  )
}
