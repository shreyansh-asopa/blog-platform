import { useState, type ChangeEvent, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router'
import { ApiError } from '../api/client'
import { authApi } from '../api/endpoints'
import { useAuth } from '../auth/useAuth'
import { ErrorMessage } from '../components/ErrorMessage'
import styles from './AuthForm.module.css'

type Field = 'email' | 'username' | 'password'

export function RegisterPage() {
  const { user, login } = useAuth()
  const navigate = useNavigate()

  const [values, setValues] = useState<Record<Field, string>>({
    email: '',
    username: '',
    password: '',
  })
  const [error, setError] = useState<unknown>(null)
  const [submitting, setSubmitting] = useState(false)

  if (user) return <Navigate to="/" replace />

  // The backend reports 422 problems per field, e.g. {"field": "body.username", ...}
  const fieldErrors: Partial<Record<Field, string>> = {}
  if (error instanceof ApiError) {
    for (const detail of error.details) {
      const field = detail.field.split('.').pop() as Field
      fieldErrors[field] ??= detail.message
    }
  }
  const hasFieldErrors = Object.keys(fieldErrors).length > 0

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      await authApi.register(values)
      // Log straight in rather than making the new user type everything again
      await login(values.username, values.password)
      navigate('/', { replace: true })
    } catch (err) {
      setError(err)
    } finally {
      setSubmitting(false)
    }
  }

  const input = (field: Field) => ({
    value: values[field],
    onChange: (e: ChangeEvent<HTMLInputElement>) =>
      setValues({ ...values, [field]: e.target.value }),
    'aria-invalid': fieldErrors[field] ? true : undefined,
  })

  return (
    <div className={`card ${styles.panel}`}>
      <h1 className={styles.heading}>Join Lumen</h1>
      <p className="muted">Share what you're learning with everyone.</p>

      <form className={styles.form} onSubmit={handleSubmit}>
        {error !== null && !hasFieldErrors && <ErrorMessage error={error} />}

        <label className={styles.field}>
          <span>Email</span>
          <input type="email" autoComplete="email" required autoFocus {...input('email')} />
          {fieldErrors.email && <small className={styles.fieldError}>{fieldErrors.email}</small>}
        </label>

        <label className={styles.field}>
          <span>Username</span>
          <input
            autoComplete="username"
            required
            minLength={3}
            maxLength={50}
            pattern="[A-Za-z0-9_]+"
            title="Letters, numbers and underscores"
            {...input('username')}
          />
          <small className="muted">3–50 letters, numbers or underscores</small>
          {fieldErrors.username && (
            <small className={styles.fieldError}>{fieldErrors.username}</small>
          )}
        </label>

        <label className={styles.field}>
          <span>Password</span>
          <input
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            maxLength={128}
            {...input('password')}
          />
          <small className="muted">At least 8 characters</small>
          {fieldErrors.password && (
            <small className={styles.fieldError}>{fieldErrors.password}</small>
          )}
        </label>

        <button className="btn btn-primary" disabled={submitting}>
          {submitting ? 'Creating account…' : 'Create account'}
        </button>
      </form>

      <p className={`muted ${styles.switch}`}>
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </div>
  )
}
