import { ApiError } from '../api/client'
import styles from './ErrorMessage.module.css'

export function ErrorMessage({ error }: { error: unknown }) {
  const message = error instanceof Error ? error.message : 'Something went wrong'
  // Quoting the request ID lets anyone find the matching line in the API's logs
  const requestId = error instanceof ApiError ? error.requestId : undefined

  return (
    <div className={styles.error} role="alert">
      {message}
      {requestId && <div className={styles.ref}>Reference: {requestId}</div>}
    </div>
  )
}
