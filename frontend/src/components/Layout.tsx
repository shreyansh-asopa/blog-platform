import { useState } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate, useSearchParams } from 'react-router'
import { useTopics } from '../api/useTopics'
import { useAuth } from '../auth/useAuth'
import { searchParams, topicsIn } from '../lib/search'
import { useTheme, type ThemeChoice } from '../theme/useTheme'
import { Avatar } from './Avatar'
import { Icon, type IconName } from './Icon'
import { TopicDot } from './TopicTags'
import styles from './Layout.module.css'

const THEMES: Record<ThemeChoice, { icon: IconName; label: string }> = {
  system: { icon: 'monitor', label: 'System theme' },
  light: { icon: 'sun', label: 'Light theme' },
  dark: { icon: 'moon', label: 'Dark theme' },
}

const TAGLINE = 'Ideas, brought to light'

/** The tagline shows only in the sidebar: the phone header bar is one line high */
function Logo({ tagline = false }: { tagline?: boolean }) {
  return (
    <Link to="/" className={styles.logo}>
      <span className={styles.wordmark}>
        <span aria-hidden>✦</span> Lumen
      </span>
      {tagline && <span className={styles.tagline}>{TAGLINE}</span>}
    </Link>
  )
}

export function Layout() {
  const { user, loading, logout } = useAuth()
  const theme = useTheme()
  const topics = useTopics()
  // On phones the sidebar is a drawer that slides in over the page
  const [menuOpen, setMenuOpen] = useState(false)
  const close = () => setMenuOpen(false)
  const { pathname } = useLocation()
  const [params] = useSearchParams()
  const navigate = useNavigate()
  // Topics fold away behind one button, and start open on a topic page so the current one shows
  const [topicsOpen, setTopicsOpen] = useState(pathname.startsWith('/t/'))

  // The ticked topics live in the search page's URL. On a topic page that topic counts as
  // ticked, so ticking another searches both.
  const onSearch = pathname === '/search'
  const ticked = onSearch
    ? topicsIn(params)
    : pathname.startsWith('/t/')
      ? [decodeURIComponent(pathname.slice(3)).toLowerCase()]
      : []
  function tick(slug: string, on: boolean) {
    const next = on ? [...ticked, slug] : ticked.filter((s) => s !== slug)
    // Keeps any search words, and starts again from page 1
    navigate(`/search?${searchParams(onSearch ? (params.get('q') ?? '') : '', next)}`)
  }

  const navClass = ({ isActive }: { isActive: boolean }) =>
    isActive ? `${styles.navLink} ${styles.active}` : styles.navLink

  return (
    <div className={styles.shell}>
      <header className={styles.mobileBar}>
        <button
          className={`btn btn-ghost ${styles.iconButton}`}
          onClick={() => setMenuOpen(true)}
          aria-label="Open menu"
          aria-expanded={menuOpen}
          aria-controls="sidebar"
        >
          <Icon name="menu" />
        </button>
        <Logo />
        {!loading && !user && (
          <Link to="/register" className={`btn btn-primary ${styles.mobileCta}`}>
            Sign up
          </Link>
        )}
      </header>

      {menuOpen && <div className={styles.backdrop} onClick={close} aria-hidden />}

      <aside id="sidebar" className={styles.sidebar} data-open={menuOpen}>
        <div className={styles.sidebarTop}>
          <Logo tagline />
          <button
            className={`btn btn-ghost ${styles.iconButton} ${styles.closeButton}`}
            onClick={close}
            aria-label="Close menu"
          >
            <Icon name="close" />
          </button>
        </div>

        {/* Any link click closes the drawer on phones */}
        <nav className={styles.nav} aria-label="Main" onClick={close}>
          <NavLink to="/" end className={navClass}>
            <Icon name="feed" /> Feed
          </NavLink>
          <NavLink to="/search" className={navClass}>
            <Icon name="search" /> Search
          </NavLink>
          {user && (
            <>
              <NavLink to="/write" className={navClass}>
                <Icon name="pen" /> Write
              </NavLink>
              <NavLink to="/me/posts" className={navClass}>
                <Icon name="posts" /> My posts
              </NavLink>
              <NavLink to="/me/drafts" className={navClass}>
                <Icon name="draft" /> Drafts
              </NavLink>
            </>
          )}
          {user?.role === 'admin' && (
            <NavLink to="/admin" className={navClass}>
              <Icon name="shield" /> Admin
            </NavLink>
          )}
        </nav>

        {/* Hidden until loaded, and if it fails: the rest of the sidebar still works */}
        {topics.data && topics.data.length > 0 && (
          <div className={styles.topics}>
            <button
              className={styles.navLink}
              onClick={() => setTopicsOpen((open) => !open)}
              aria-expanded={topicsOpen}
              aria-controls="topics-list"
            >
              <Icon name="tag" /> <span className={styles.topicName}>Topics</span>
              <span className={styles.chevron} data-open={topicsOpen}>
                <Icon name="chevronDown" size={18} />
              </span>
            </button>
            {topicsOpen && (
              <div id="topics-list" className={styles.topicList}>
                <p className={styles.topicHint}>Tick topics to search them together</p>
                {/* Ticking doesn't close the phone drawer, so you can pick several */}
                <nav aria-label="Topics">
                  {topics.data.map((topic) => (
                    <div key={topic.slug} className={styles.topicRow}>
                      <input
                        type="checkbox"
                        className={styles.tick}
                        checked={ticked.includes(topic.slug)}
                        onChange={(event) => tick(topic.slug, event.target.checked)}
                        aria-label={`Search ${topic.name}`}
                      />
                      <NavLink
                        to={`/t/${topic.slug}`}
                        className={navClass}
                        title={topic.name}
                        onClick={close}
                      >
                        <TopicDot slug={topic.slug} />
                        <span className={styles.topicName}>{topic.name}</span>
                        <span className={styles.count}>
                          {topic.post_count}
                          <span className="visually-hidden"> posts</span>
                        </span>
                      </NavLink>
                    </div>
                  ))}
                </nav>
                {ticked.length > 1 && (
                  <button className={styles.clear} onClick={() => navigate('/search')}>
                    Clear {ticked.length} topics
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        <div className={styles.sidebarBottom}>
          <button
            className={styles.navLink}
            onClick={theme.cycle}
            title="Click to switch between system, light and dark"
          >
            <Icon name={THEMES[theme.choice].icon} /> {THEMES[theme.choice].label}
          </button>

          {loading ? null : user ? (
            <>
              <div className={styles.user} title={user.email}>
                <Avatar name={user.username} />
                <span className={styles.username}>{user.username}</span>
              </div>
              <button className={styles.navLink} onClick={logout}>
                <Icon name="logout" /> Log out
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login" className={navClass} onClick={close}>
                <Icon name="login" /> Log in
              </NavLink>
              <Link to="/register" className={`btn btn-primary ${styles.cta}`} onClick={close}>
                Create account
              </Link>
            </>
          )}
        </div>
      </aside>

      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  )
}
