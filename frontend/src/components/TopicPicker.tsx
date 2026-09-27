import { useEffect, useId, useRef, useState } from 'react'
import { useNavigate } from 'react-router'
import type { TopicDetail } from '../api/types'
import { plural } from '../lib/format'
import { Icon } from './Icon'
import { TopicDot } from './TopicTags'
import styles from './TopicPicker.module.css'

interface Props {
  topics: TopicDetail[]
  /** Slugs to mark as trending */
  trending: string[]
  onClose: () => void
}

/**
 * Every topic in a popup, with a box to narrow them down. Picking one opens its page.
 * The native <dialog> dims the page, keeps keyboard focus inside and closes on Esc.
 */
export function TopicPicker({ topics, trending, onClose }: Props) {
  const ref = useRef<HTMLDialogElement>(null)
  const filter = useRef<HTMLInputElement>(null)
  const titleId = useId()
  const navigate = useNavigate()
  const [typed, setTyped] = useState('')

  useEffect(() => {
    const dialog = ref.current
    dialog?.showModal()
    // showModal() focuses the first button (×), but people come here to type
    filter.current?.focus()
    return () => dialog?.close()
  }, [])

  const words = typed.trim().toLowerCase()
  const shown = words
    ? topics.filter((t) => `${t.name} ${t.description}`.toLowerCase().includes(words))
    : topics

  function pick(slug: string) {
    onClose()
    navigate(`/t/${slug}`)
  }

  return (
    <dialog
      ref={ref}
      className={`card ${styles.dialog}`}
      aria-labelledby={titleId}
      onCancel={(event) => {
        // React decides when the dialog goes away, not the browser
        event.preventDefault()
        onClose()
      }}
      // A click on the dimmed backdrop lands on the <dialog> itself
      onClick={(event) => event.target === event.currentTarget && onClose()}
    >
      <div className={styles.header}>
        <div>
          <h2 id={titleId} className={styles.title}>
            Explore topics
          </h2>
          <p className="muted">Pick one that sparks your interest.</p>
        </div>
        <button className={`btn btn-ghost ${styles.close}`} onClick={onClose} aria-label="Close">
          <Icon name="close" />
        </button>
      </div>

      <label className={styles.filter}>
        <span className="visually-hidden">Find a topic</span>
        <Icon name="search" size={18} />
        <input
          type="search"
          placeholder="Find a topic…"
          value={typed}
          onChange={(event) => setTyped(event.target.value)}
          ref={filter}
        />
      </label>

      {shown.length > 0 ? (
        <ul className={styles.grid}>
          {shown.map((topic) => (
            <li key={topic.slug}>
              <button className={styles.topic} onClick={() => pick(topic.slug)}>
                <span className={styles.name}>
                  <TopicDot slug={topic.slug} />
                  {topic.name}
                  {trending.includes(topic.slug) && <span className={styles.badge}>Trending</span>}
                </span>
                <span className={styles.description}>{topic.description}</span>
                <span className={styles.count}>{plural(topic.post_count, 'post')}</span>
              </button>
            </li>
          ))}
        </ul>
      ) : (
        <p className={`muted ${styles.empty}`}>No topics match “{typed.trim()}”.</p>
      )}
    </dialog>
  )
}
