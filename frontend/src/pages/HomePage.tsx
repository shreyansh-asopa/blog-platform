import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router'
import { postsApi } from '../api/endpoints'
import type { Sort } from '../api/types'
import { useAuth } from '../auth/useAuth'
import { ErrorMessage } from '../components/ErrorMessage'
import { Hero } from '../components/Hero'
import { Pagination } from '../components/Pagination'
import { PostCard } from '../components/PostCard'
import { SearchForm } from '../components/SearchForm'
import { SortSelect } from '../components/SortSelect'
import { plural } from '../lib/format'
import styles from './HomePage.module.css'

const PAGE_SIZE = 10

export function HomePage() {
  const { user, loading } = useAuth()
  const [params, setParams] = useSearchParams()
  const navigate = useNavigate()
  const page = Math.max(1, Number(params.get('page')) || 1)
  const sort: Sort = params.get('sort') === 'oldest' ? 'oldest' : 'newest'

  const feed = useQuery({
    queryKey: ['posts', 'feed', sort, page],
    queryFn: () => postsApi.feed(page, PAGE_SIZE, { sort }),
    // Keep showing the current page while the next one loads, instead of a blank flash
    placeholderData: keepPreviousData,
  })

  // Braces matter: newer browsers return a Promise from scrollTo, and React would
  // mistake a returned value for a clean-up function
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [page])

  // Newest is the default, so it stays out of the URL; either way back to page 1
  function changeSort(next: Sort) {
    setParams(next === 'oldest' ? { sort: next } : {})
  }

  function pageHref(n: number) {
    const query = new URLSearchParams()
    if (sort === 'oldest') query.set('sort', sort)
    if (n > 1) query.set('page', String(n))
    return query.size ? `/?${query}` : '/'
  }

  return (
    <div className={styles.home}>
      {/* Visitors get the welcome block first; members go straight to reading */}
      {!loading && !user && page === 1 && <Hero />}

      <section className={styles.feed} aria-labelledby="feed-title">
        {/* Searching opens the full results page; the sort reorders this feed in place */}
        <div className={styles.toolbar}>
          <SearchForm
            id="home-search"
            placeholder="Find stories that spark your curiosity…"
            onSearch={(q) => q && navigate(`/search?${new URLSearchParams({ q })}`)}
          />
          <SortSelect value={sort} onChange={changeSort} />
        </div>

        <header className={styles.feedHeader}>
          <h2 id="feed-title">{sort === 'oldest' ? 'Oldest posts' : 'Latest posts'}</h2>
          {feed.data && (
            <span className="muted">
              <span className={styles.dot} aria-hidden />
              {plural(feed.data.total, 'article')}
            </span>
          )}
        </header>

        {feed.isPending && <p className="muted">Loading posts…</p>}
        {feed.isError && <ErrorMessage error={feed.error} />}
        {feed.data?.items.length === 0 && (
          <div className={`card ${styles.empty}`}>
            <p>
              {page > 1 ? 'No posts on this page.' : 'No posts yet. Be the first to write one!'}
            </p>
          </div>
        )}
        <div className={styles.list} aria-busy={feed.isPlaceholderData}>
          {feed.data?.items.map((post) => (
            <PostCard key={post.id} post={post} />
          ))}
        </div>
        {feed.data && (
          <Pagination page={page} size={PAGE_SIZE} total={feed.data.total} href={pageHref} />
        )}
      </section>
    </div>
  )
}
