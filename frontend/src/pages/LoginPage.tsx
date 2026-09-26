import { useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router'
import { useAuth } from '../auth/useAuth'
import { ErrorMessage } from '../components/ErrorMessage'
import styles from './AuthForm.module.css'

export function LoginPage() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  // Where the user was heading before being sent here (set by <RequireAuth>)
  const from = (useLocation().state as { from?: string } | null)?.from ?? '/'

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<unknown>(null)
  const [submitting, setSubmitting] = useState(false)

  if (user) return <Navigate to={from} replace />

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      await login(username, password)
      navigate(from, { replace: true })
    } catch (err) {
      setError(err)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className={`card ${styles.panel}`}>
      <h1 className={styles.heading}>Welcome back</h1>
      <p className="muted">Log in to write, like and comment.</p>

      <form className={styles.form} onSubmit={handleSubmit}>
        {error !== null && <ErrorMessage error={error} />}

        <label className={styles.field}>
          <span>Username or email</span>
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            required
            autoFocus
          />
        </label>

        <label className={styles.field}>
          <span>Password</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </label>

        <button className="btn btn-primary" disabled={submitting}>
          {submitting ? 'Logging in…' : 'Log in'}
        </button>
      </form>

      <p className={`muted ${styles.switch}`}>
        New to Lumen? <Link to="/register">Create an account</Link>
      </p>
    </div>
  )
}
