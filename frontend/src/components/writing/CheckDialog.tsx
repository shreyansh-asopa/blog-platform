import { useEffect, useId, useRef } from 'react'
import type { ReactNode } from 'react'
import { Icon } from '../Icon'
import styles from './Writing.module.css'

interface Props {
  open: boolean
  title: string
  subtitle: string
  /** Who sees the text, shown at the bottom */
  privacy: string
  canUndo: boolean
  onUndo: () => void
  onClose: () => void
  children: ReactNode
}

/**
 * A panel on the right (a sheet from the bottom on phones) over a lightly dimmed page,
 * so the post stays readable behind it and accepted fixes show up at once.
 * It stays in the page while closed, so its results are still there when reopened.
 */
export function CheckDialog({
  open,
  title,
  subtitle,
  privacy,
  canUndo,
  onUndo,
  onClose,
  children,
}: Props) {
  const ref = useRef<HTMLDialogElement>(null)
  const titleId = useId()

  useEffect(() => {
    const dialog = ref.current
    if (!dialog) return
    if (open && !dialog.open) dialog.showModal()
    if (!open && dialog.open) dialog.close()
  }, [open])

  return (
    <dialog
      ref={ref}
      className={styles.dialog}
      aria-labelledby={titleId}
      onCancel={(event) => {
        // React decides when the dialog goes away, not the browser
        event.preventDefault()
        onClose()
      }}
      // A click on the dimmed backdrop lands on the <dialog> itself
      onClick={(event) => event.target === event.currentTarget && onClose()}
    >
      <header className={styles.header}>
        <div>
          <h2 id={titleId} className={styles.title}>
            {title}
          </h2>
          <p className="muted">{subtitle}</p>
        </div>
        <button
          type="button"
          className={`btn btn-ghost ${styles.close}`}
          aria-label="Close"
          onClick={onClose}
        >
          <Icon name="close" />
        </button>
      </header>
      <div className={styles.body}>{children}</div>
      <footer className={styles.footer}>
        <span className="muted">{privacy}</span>
        <button
          type="button"
          className="btn btn-ghost"
          disabled={!canUndo}
          onClick={onUndo}
          title="Changes made here are normal edits, so ⌘Z undoes them too"
        >
          <Icon name="undo" size={16} />
          Undo last change
        </button>
      </footer>
    </dialog>
  )
}

/** "Your post changed since this check", with a button to run it again */
export function StaleNotice({ onRecheck }: { onRecheck: () => void }) {
  return (
    <div className={styles.stale} role="status">
      <span>Your post changed since this check.</span>
      <button type="button" className="btn btn-outline" onClick={onRecheck}>
        Check again
      </button>
    </div>
  )
}

export function Spinner({ label }: { label: string }) {
  return (
    <div className={styles.loading} role="status">
      <span className={styles.spinner} aria-hidden />
      {label}
    </div>
  )
}
