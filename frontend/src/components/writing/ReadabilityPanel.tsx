import type { Editor } from '@tiptap/react'
import { useEffect, useMemo, useState } from 'react'
import { writingApi } from '../../api/endpoints'
import { replaceTarget, targetAt, type Target } from '../../lib/editorText'
import { plural } from '../../lib/format'
import { LONG_SENTENCE, readability, type Sentence } from '../../lib/readability'
import { ErrorMessage } from '../ErrorMessage'
import { Icon } from '../Icon'
import styles from './Writing.module.css'

interface Props {
  editor: Editor
  text: string
  /** Whether "Simplify with AI" can be used (it needs the server's AI key) */
  aiReady: boolean
  onBadge: (badge: string | null) => void
  onShow: (target: Target) => void
}

/** Worked out as the writer types; only "Simplify with AI" sends anything */
export function ReadabilityPanel({ editor, text, aiReady, onBadge, onShow }: Props) {
  const result = useMemo(() => readability(text), [text])

  useEffect(() => {
    onBadge(result ? String(result.score) : null)
  }, [result, onBadge])

  if (!result)
    return <p className={styles.empty}>Write a few sentences to see how easy they are to read.</p>

  return (
    <div className={styles.stack}>
      <div className={styles.score} data-level={result.level}>
        <div className={styles.scoreTop}>
          <span className={styles.scoreNumber}>{result.score}</span>
          <span className={styles.scoreLabel}>{result.label}</span>
        </div>
        <div
          className={styles.meter}
          role="meter"
          aria-label="Reading ease"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={result.score}
        >
          <span style={{ width: `${Math.max(result.score, 3)}%` }} />
        </div>
        <p className="muted">
          Out of 100: higher is easier. Most blog readers are happy from about 60.
        </p>
      </div>

      <dl className={styles.stats}>
        <div>
          <dt>Words</dt>
          <dd>{result.words.toLocaleString()}</dd>
        </div>
        <div>
          <dt>Sentences</dt>
          <dd>{result.sentences.toLocaleString()}</dd>
        </div>
        <div>
          <dt>Words per sentence</dt>
          <dd>{result.averageWords}</dd>
        </div>
        <div>
          <dt>Reading time</dt>
          <dd>{result.minutes} min</dd>
        </div>
      </dl>

      <section className={styles.group} aria-label="Long sentences">
        <h3 className={styles.groupTitle}>
          Long sentences <span className="muted">{result.long.length}</span>
        </h3>
        {result.long.length === 0 ? (
          <p className="muted">No sentence is over {LONG_SENTENCE} words. Nice and tight.</p>
        ) : (
          <>
            <p className="muted">
              Over {LONG_SENTENCE} words. Splitting them makes the post easier to follow.
            </p>
            {result.long.map((sentence) => (
              <LongSentence
                // The same sentence can't be listed twice at one place
                key={`${sentence.offset}:${sentence.text}`}
                sentence={sentence}
                target={targetAt(text, sentence.offset, sentence.text.length)}
                editor={editor}
                aiReady={aiReady}
                onShow={onShow}
              />
            ))}
          </>
        )}
      </section>
    </div>
  )
}

interface SentenceProps {
  sentence: Sentence
  target: Target
  editor: Editor
  aiReady: boolean
  onShow: (target: Target) => void
}

function LongSentence({ sentence, target, editor, aiReady, onShow }: SentenceProps) {
  const [fix, setFix] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<unknown>(null)

  async function simplify() {
    setBusy(true)
    setError(null)
    try {
      setFix((await writingApi.simplify(sentence.text)).fix)
    } catch (caught) {
      setError(caught)
    } finally {
      setBusy(false)
    }
  }

  return (
    <article className={styles.issue}>
      <p className={styles.context}>{sentence.text}</p>
      <p className="muted">{plural(sentence.words, 'word')}</p>

      {fix !== null && (
        <div className={styles.rewrite}>
          <span className={styles.rewriteLabel}>
            <Icon name="sparkle" size={14} /> Shorter version
          </span>
          <p>{fix}</p>
        </div>
      )}
      {error !== null && <ErrorMessage error={error} />}

      <div className={styles.actions}>
        {fix !== null ? (
          <>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => replaceTarget(editor, target, fix)}
            >
              <Icon name="check" size={16} /> Accept
            </button>
            <button type="button" className="btn btn-ghost" onClick={() => setFix(null)}>
              Ignore
            </button>
          </>
        ) : (
          <button
            type="button"
            className="btn btn-outline"
            disabled={!aiReady || busy}
            title={aiReady ? 'Ask the AI for a shorter version' : "The AI checks aren't set up yet"}
            onClick={() => void simplify()}
          >
            <Icon name="sparkle" size={16} />
            {busy ? 'Simplifying…' : 'Simplify with AI'}
          </button>
        )}
        <span className={styles.spacer} />
        <button type="button" className="btn btn-ghost" onClick={() => onShow(target)}>
          Show in post
        </button>
      </div>
    </article>
  )
}
