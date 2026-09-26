import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { NavLink, useSearchParams } from 'react-router'
import { adminApi } from '../api/endpoints'
import type { AuditAction, AuditLog, Role, User } from '../api/types'
import { useAuth } from '../auth/useAuth'
import { Avatar } from '../components/Avatar'
import { ErrorMessage } from '../components/ErrorMessage'
import { Pagination } from '../components/Pagination'
import { formatDate, formatDateTime, plural } from '../lib/format'
import styles from './AdminPage.module.css'

const PAGE_SIZE = 20

/** /admin manages users, /admin/audit shows what admins have done */
export function AdminPage({ section }: { section: 'users' | 'audit' }) {
  useEffect(() => {
    document.title = 'Admin · Lumen'
    return () => {
      document.title = 'Lumen'
    }
  }, [])

  return (
    <div className={styles.page}>
      <header>
        <h1 className={styles.heading}>Admin</h1>
        <p className="muted">Manage who can moderate Lumen, and see every admin action.</p>
      </header>

      <nav className={styles.tabs} aria-label="Admin sections">
        <NavLink to="/admin" end className={tabClass}>
          Users
        </NavLink>
        <NavLink to="/admin/audit" className={tabClass}>
          Audit log
        </NavLink>
      </nav>

      {section === 'users' ? <Users /> : <Audit />}
    </div>
  )
}

const tabClass = ({ isActive }: { isActive: boolean }) =>
  isActive ? `${styles.tab} ${styles.active}` : styles.tab

/** Reads ?page=, and builds page links that keep every other filter in the URL */
function usePage() {
  const [params, setParams] = useSearchParams()
  const page = Math.max(1, Number(params.get('page')) || 1)
  const href = (n: number) => {
    const next = new URLSearchParams(params)
    if (n === 1) next.delete('page')
    else next.set('page', String(n))
    return `?${next}`
  }
  /** Changes one filter. Back to page 1, since the old page number may not exist any more */
  const setFilter = (key: string, value: string) => {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
    next.delete('page')
    // replace: typing a search shouldn't add a history entry per keystroke
    setParams(next, { replace: true })
  }
  return { params, page, href, setFilter }
}

// --- Users ---

function Users() {
  const { user: me } = useAuth()
  const { params, page, href, setFilter } = usePage()
  const search = params.get('q') ?? ''
  const role = (params.get('role') as Role | null) ?? undefined

  // The box updates at once; the URL (and so the request) waits until typing pauses
  const [typed, setTyped] = useState(search)
  useEffect(() => {
    const timer = setTimeout(() => {
      if (typed.trim() !== search) setFilter('q', typed.trim())
    }, 300)
    return () => clearTimeout(timer)
  }, [typed]) // eslint-disable-line react-hooks/exhaustive-deps

  const users = useQuery({
    queryKey: ['admin', 'users', search, role ?? 'all', page],
    queryFn: () => adminApi.users(page, PAGE_SIZE, search, role),
    placeholderData: keepPreviousData,
  })

  return (
    <section className={styles.section} aria-label="Users">
      <div className={styles.filters}>
        <label className="visually-hidden" htmlFor="user-search">
          Search users
        </label>
        <input
          id="user-search"
          type="search"
          className={styles.input}
          placeholder="Search by username or email…"
          value={typed}
          onChange={(event) => setTyped(event.target.value)}
          maxLength={100}
        />
        <label className="visually-hidden" htmlFor="user-role">
          Role
        </label>
        <select
          id="user-role"
          className={styles.input}
          value={role ?? ''}
          onChange={(event) => setFilter('role', event.target.value)}
        >
          <option value="">All roles</option>
          <option value="admin">Admins</option>
          <option value="user">Users</option>
        </select>
        {users.data && <span className="muted">{plural(users.data.total, 'user')}</span>}
      </div>

      {users.isPending && <p className="muted">Loading users…</p>}
      {users.isError && <ErrorMessage error={users.error} />}
      {users.data?.items.length === 0 && <p className={`card ${styles.empty}`}>No users match.</p>}

      {users.data && users.data.items.length > 0 && (
        <div className={`card ${styles.tableWrap}`}>
          <table className={styles.table} aria-busy={users.isPlaceholderData}>
            <thead>
              <tr>
                <th>User</th>
                <th>Role</th>
                <th className={styles.hideSmall}>Joined</th>
                <th>
                  <span className="visually-hidden">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {users.data.items.map((u) => (
                <UserRow key={u.id} user={u} isMe={u.id === me?.id} />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {users.data && (
        <Pagination page={page} size={PAGE_SIZE} total={users.data.total} href={href} />
      )}
    </section>
  )
}

function UserRow({ user, isMe }: { user: User; isMe: boolean }) {
  const queryClient = useQueryClient()
  const next: Role = user.role === 'admin' ? 'user' : 'admin'

  const change = useMutation({
    mutationFn: () => adminApi.setRole(user.id, next),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin'] })
    },
  })

  function confirmChange() {
    const question =
      next === 'admin'
        ? `Make ${user.username} an admin? They will be able to edit and delete any post or comment.`
        : `Remove admin rights from ${user.username}?`
    if (window.confirm(question)) change.mutate()
  }

  return (
    <tr>
      <td>
        <div className={styles.who}>
          <Avatar name={user.username} />
          <div className={styles.whoText}>
            <strong>
              {user.username}
              {isMe && <span className="muted"> (you)</span>}
            </strong>
            <span className="muted">{user.email}</span>
          </div>
        </div>
        {change.isError && <ErrorMessage error={change.error} />}
      </td>
      <td>
        <span className={styles.role} data-role={user.role}>
          {user.role === 'admin' ? 'Admin' : 'User'}
        </span>
      </td>
      <td className={`muted ${styles.hideSmall}`}>{formatDate(user.created_at)}</td>
      <td className={styles.actionCell}>
        <button
          className={`btn ${next === 'admin' ? 'btn-outline' : 'btn-ghost'}`}
          onClick={confirmChange}
          // The API refuses this too: it's what guarantees at least one admin remains
          disabled={isMe || change.isPending}
          title={isMe ? "You can't change your own role" : undefined}
        >
          {next === 'admin' ? 'Make admin' : 'Remove admin'}
        </button>
      </td>
    </tr>
  )
}

// --- Audit log ---

const ACTIONS: Record<AuditAction, string> = {
  'user.role_changed': 'Role changes',
  'post.updated': 'Post edits',
  'post.published': 'Posts published',
  'post.unpublished': 'Posts unpublished',
  'post.deleted': 'Posts deleted',
  'comment.deleted': 'Comments deleted',
}

function Audit() {
  const { params, page, href, setFilter } = usePage()
  const raw = params.get('action')
  const action = raw && raw in ACTIONS ? (raw as AuditAction) : undefined

  const logs = useQuery({
    queryKey: ['admin', 'audit', action ?? 'all', page],
    queryFn: () => adminApi.auditLogs(page, PAGE_SIZE, action),
    placeholderData: keepPreviousData,
  })

  return (
    <section className={styles.section} aria-label="Audit log">
      <div className={styles.filters}>
        <label className="visually-hidden" htmlFor="audit-action">
          Action
        </label>
        <select
          id="audit-action"
          className={styles.input}
          value={action ?? ''}
          onChange={(event) => setFilter('action', event.target.value)}
        >
          <option value="">All actions</option>
          {Object.entries(ACTIONS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        {logs.data && <span className="muted">{plural(logs.data.total, 'record')}</span>}
      </div>
      <p className={`muted ${styles.note}`}>
        Recorded whenever an admin changes a role or acts on someone else&apos;s post or comment.
        Entries can&apos;t be edited or removed.
      </p>

      {logs.isPending && <p className="muted">Loading the audit log…</p>}
      {logs.isError && <ErrorMessage error={logs.error} />}
      {logs.data?.items.length === 0 && (
        <p className={`card ${styles.empty}`}>Nothing recorded yet.</p>
      )}

      <ol className={styles.log} aria-busy={logs.isPlaceholderData}>
        {logs.data?.items.map((entry) => (
          <li key={entry.id} className={styles.entry}>
            <Avatar name={entry.actor?.username ?? '?'} />
            <div>
              <p className={styles.sentence}>
                <strong>{entry.actor?.username ?? 'A deleted user'}</strong> {describe(entry)}
              </p>
              <time className="muted" dateTime={entry.created_at}>
                {formatDateTime(entry.created_at)}
              </time>
            </div>
            <code className={styles.code}>{entry.action}</code>
          </li>
        ))}
      </ol>

      {logs.data && <Pagination page={page} size={PAGE_SIZE} total={logs.data.total} href={href} />}
    </section>
  )
}

/** Turns an entry into the rest of a sentence, e.g. "changed ada's role from user to admin" */
function describe({ action, details }: AuditLog): string {
  const d = details as Record<string, string | string[] | undefined>
  switch (action) {
    case 'user.role_changed':
      return `changed ${d.username}'s role from ${d.from} to ${d.to}`
    case 'post.deleted':
      return `deleted the post “${d.title}”`
    case 'post.updated':
      return Array.isArray(d.fields) && d.fields.length
        ? `edited someone's post (${d.fields.join(', ').replace('cover_image', 'cover')})`
        : "edited someone's post"
    case 'post.published':
      return "published someone's post"
    case 'post.unpublished':
      return "moved someone's post back to drafts"
    case 'comment.deleted':
      return "deleted someone's comment"
  }
}
