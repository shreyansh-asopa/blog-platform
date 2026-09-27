import { useEffect, useId, useRef } from 'react'
import type { ReactNode } from 'react'
import styles from './ConfirmDialog.module.css'

interface Props {
  title: string
  children: ReactNode
  confirmLabel: string
  cancelLabel: string
  onConfirm: () => void
  onCancel: () => void
}

/**
 * A yes/no question over the page. The native <dialog> dims the page, keeps keyboard focus
 * inside, and closes on Esc (which counts as cancel).
 */
export function ConfirmDialog({
  title,
  children,
  confirmLabel,
  cancelLabel,
  onConfirm,
  onCancel,
}: Props) {
  const ref = useRef<HTMLDialogElement>(null)
  const titleId = useId()

  useEffect(() => {
    const dialog = ref.current
    dialog?.showModal()
    return () => dialog?.close()
  }, [])

  return (
    <dialog
      ref={ref}
      className={`card ${styles.dialog}`}
      aria-labelledby={titleId}
      onCancel={(event) => {
        // React decides when the dialog goes away, not the browser
        event.preventDefault()
        onCancel()
      }}
    >
      <h2 id={titleId} className={styles.title}>
        {title}
      </h2>
      <div className={`muted ${styles.body}`}>{children}</div>
      <div className={styles.actions}>
        {/* Focused first: pressing Enter by reflex keeps the work */}
        <button className="btn btn-primary" onClick={onCancel} autoFocus>
          {cancelLabel}
        </button>
        <button className={`btn ${styles.danger}`} onClick={onConfirm}>
          {confirmLabel}
        </button>
      </div>
    </dialog>
  )
}
