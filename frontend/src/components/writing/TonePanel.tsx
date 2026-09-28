import type { Editor } from '@tiptap/react'
import { useEffect, useState } from 'react'
import { writingApi } from '../../api/endpoints'
import type { Suggestion, ToneResult, ToneTarget } from '../../api/types'
import { readDoc, replaceTarget, targetFor, type Target } from '../../lib/editorText'
import { plural } from '../../lib/format'
import { ErrorMessage } from '../ErrorMessage'
import { Icon } from '../Icon'
import { Spinner, StaleNotice } from './CheckDialog'
import styles from './Writing.module.css'

const TARGETS: { value: ToneTarget; label: string }[] = [
  { value: 'professional', label: 'Professional' },
  { value: 'friendly', label: 'Friendly' },
  { value: 'confident', label: 'Confident' },
  { value: 'casual', label: 'Casual' },
]

interface Item extends Suggestion {
  id: number
  done: boolean
}

interface Props {
  editor: Editor
  text: string
  /** False until the server has an AI key (Gemini or Groq) */
  ready: boolean
  maxChars: number
  onBadge: (badge: string | null) => void
  onShow: (target: Target) => void
}

export function TonePanel({ editor, text, ready, maxChars, onBadge, onShow }: Props) {
  const [target, setTarget] = useState<ToneTarget>('friendly')
  const [result, setResult] = useState<(ToneResult & { items: Item[] }) | null>(null)
  const [expected, setExpected] = useState('')
  const [checking, setChecking] = useState(false)
  const [error, setError] = useState<unknown>(null)

  const pending = result?.items.filter((item) => !item.done) ?? []
  useEffect(() => {
    onBadge(result === null ? null : pending.length === 0 ? '✓' : String(pending.length))
  }, [result, pending.length, onBadge])

  if (!ready)
    return (
      <div className={styles.setup}>
        <Icon name="sparkle" size={28} />
        <p>
          <strong>The tone check isn't set up yet.</strong>
        </p>
        <p className="muted">
          It uses a free AI: Google Gemini or Groq. Whoever runs this site can turn it on by adding
          a free API key (<code>GEMINI_API_KEY</code> or <code>GROQ_API_KEY</code>) to the server's
          settings.
        </p>
      </div>
    )

  const empty = text.trim() === ''
  const tooLong = text.length > maxChars

  async function check() {
    const sent = readDoc(editor).text
    setChecking(true)
    setError(null)
    try {
      const answer = await writingApi.tone(sent, target)
      setResult({
        ...answer,
        items: answer.suggestions.map((s, id) => ({ ...s, id, done: false })),
      })
      setExpected(sent)
    } catch (caught) {
      setError(caught)
    } finally {
      setChecking(false)
    }
  }

  const finish = (ids: number[]) => {
    setResult((r) =>
      r ? { ...r, items: r.items.map((i) => (ids.includes(i.id) ? { ...i, done: true } : i)) } : r,
    )
    setExpected(readDoc(editor).text)
  }

  const apply = (item: Item) => {
    const where = targetFor(readDoc(editor).text, item.original)
    if (where) replaceTarget(editor, where, item.fix)
  }

  function acceptAll() {
    for (const item of pending) apply(item)
    finish(pending.map((item) => item.id))
  }

  const find = (item: Item) => {
    const where = targetFor(readDoc(editor).text, item.original)
    if (where) onShow(where)
  }

  return (
    <div className={styles.stack}>
      <fieldset className={styles.targets}>
        <legend>How should the post sound?</legend>
        <div className={styles.chips}>
          {TARGETS.map((t) => (
            <button
              key={t.value}
              type="button"
              className="chip"
              aria-pressed={target === t.value}
              onClick={() => setTarget(t.value)}
            >
              {t.label}
            </button>
          ))}
        </div>
      </fieldset>
      <button
        type="button"
        className="btn btn-primary"
        disabled={checking || empty || tooLong}
        onClick={() => void check()}
      >
        <Icon name="sparkle" size={16} />
        {result ? 'Check tone again' : 'Check tone'}
      </button>
      {empty && <p className="muted">Write something first, then check it here.</p>}
      {tooLong && (
        <p className="muted">
          The post is too long to check at once (the most is {maxChars.toLocaleString()}{' '}
          characters).
        </p>
      )}

      {checking && <Spinner label="Reading your post…" />}
      {error !== null && !checking && <ErrorMessage error={error} />}

      {result && !checking && (
        <>
          {text !== expected && <StaleNotice onRecheck={() => void check()} />}
          <div className={styles.tone}>
            <span className="muted">Sounds</span>
            <strong>{result.tone}</strong>
            <p>{result.explanation}</p>
          </div>

          {pending.length === 0 ? (
            <p className={styles.empty}>
              {result.items.length === 0 ? 'No changes needed, it already fits.' : 'All done 🎉'}
            </p>
          ) : (
            <div className={styles.summary}>
              <span>{plural(pending.length, 'suggestion')}</span>
              {pending.length > 1 && (
                <button type="button" className="btn btn-primary" onClick={acceptAll}>
                  Accept all
                </button>
              )}
            </div>
          )}

          {pending.map((item) => (
            <article key={item.id} className={styles.issue}>
              <p className={styles.before}>
                <del>{item.original}</del>
              </p>
              <p className={styles.after}>{item.fix}</p>
              {item.reason && <p className={styles.message}>{item.reason}</p>}
              <div className={styles.actions}>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => {
                    apply(item)
                    finish([item.id])
                  }}
                >
                  <Icon name="check" size={16} /> Accept
                </button>
                <button type="button" className="btn btn-ghost" onClick={() => finish([item.id])}>
                  Ignore
                </button>
                <span className={styles.spacer} />
                <button type="button" className="btn btn-ghost" onClick={() => find(item)}>
                  Show in post
                </button>
              </div>
            </article>
          ))}
        </>
      )}
    </div>
  )
}
