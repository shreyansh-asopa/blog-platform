import { Link, NavLink, Outlet } from 'react-router'
import { useAuth } from '../auth/useAuth'
import { useTheme, type ThemeChoice } from '../theme/useTheme'
import { Avatar } from './Avatar'
import styles from './Layout.module.css'

const THEME_LABELS: Record<ThemeChoice, string> = {
  system: '🖥️ System theme',
  light: '☀️ Light theme',
  dark: '🌙 Dark theme',
}

export function Layout() {
  const { user, loading, logout } = useAuth()
  const theme = useTheme()

  const navClass = ({ isActive }: { isActive: boolean }) =>
    isActive ? `${styles.navLink} ${styles.active}` : styles.navLink

  return (
    <div className={styles.shell}>
      <header className={styles.topbar}>
        <Link to="/" className={styles.logo}>
          <span aria-hidden>✦</span> Lumen
        </Link>

        {/* Wired up once the backend has a search endpoint */}
        <input
          className={styles.search}
          type="search"
          placeholder="Search (coming soon)"
          aria-label="Search posts"
          disabled
        />

        <div className={styles.actions}>
          <button
            className="btn btn-ghost"
            onClick={theme.cycle}
            title={`${THEME_LABELS[theme.choice]}. Click to change.`}
            aria-label={THEME_LABELS[theme.choice]}
          >
            {THEME_LABELS[theme.choice].split(' ')[0]}
          </button>

          {loading ? null : user ? (
            <>
              <Link to="/write" className="btn btn-outline">
                Write
              </Link>
              <span className={styles.user} title={user.email}>
                <Avatar name={user.username} />
                <span className={styles.username}>{user.username}</span>
              </span>
              <button className="btn btn-ghost" onClick={logout}>
                Log out
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn btn-ghost">
                Log in
              </Link>
              <Link to="/register" className="btn btn-primary">
                <span className={styles.wide}>Create account</span>
                <span className={styles.narrow}>Sign up</span>
              </Link>
            </>
          )}
        </div>
      </header>

      <div className={styles.body}>
        <nav className={styles.sidebar} aria-label="Main">
          <NavLink to="/" end className={navClass}>
            🏠 <span>Home</span>
          </NavLink>
          {user && (
            <>
              <NavLink to="/me/posts" className={navClass}>
                📝 <span>My posts</span>
              </NavLink>
              <NavLink to="/me/drafts" className={navClass}>
                🗒️ <span>Drafts</span>
              </NavLink>
            </>
          )}
          {user?.role === 'admin' && (
            <NavLink to="/admin" className={navClass}>
              🛡️ <span>Admin</span>
            </NavLink>
          )}
        </nav>

        <main className={styles.main}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}
