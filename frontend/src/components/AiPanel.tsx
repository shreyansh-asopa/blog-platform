import { useEffect, useRef, useState } from 'react'
import { aiApi } from '../api/endpoints'
import type { AiInfo, AiWriteAction, GrammarFix } from '../api/types'
import { useAiInfo } from '../api/useAiInfo'
import { ErrorMessage } from './ErrorMessage'
import { Icon } from './Icon'
import { Markdown } from './Markdown'
import styles from './AiPanel.module.css'

type Action = 'grammar' | AiWriteAction

const ACTIONS: { id: Action; label: string; hint: string }[] = [
  { id: 'grammar', label: 'Check grammar', hint: 'Spelling, grammar and punctuation' },
  { id: 'polish', label: 'Polish', hint: 'Clearer, smoother wording, in your voice' },
  { id: 'ideas', label: 'Add ideas', hint: 'Points and sections worth adding' },
  { id: 'recommend', label: 'Recommendations', hint: 'Title, opening, structure, ending' },
]

const HEADINGS: Record<AiWriteAction, string> = {
  polish: 'Polished version',
  ideas: 'Ideas to add',
  recommend: 'Recommendations',
}

type Result =
  | { kind: 'grammar'; fixes: GrammarFix[] }
  | { kind: 'text'; action: AiWriteAction; text: string; done: boolean; basedOn: string }

interface AiPanelProps {
  title: string
  content: string
  /** Changes the post's text. Only ever called when the author accepts a suggestion */
  onChange: (content: string) => void
}

/** Writing help beside the editor. Every answer is a suggestion the author can take or leave. */
export function AiPanel({ title, content, onChange }: AiPanelProps) {
  const info = useAiInfo()
  const [busy, setBusy] = useState<Action | null>(null)
  const [error, setError] = useState<unknown>(null)
  const [result, setResult] = useState<Result | null>(null)
  // The text from before the AI's last change, so it can be put back
  const [undo, setUndo] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const controller = useRef<AbortController | null>(null)

  // Leaving the editor stops an answer that is still being written
  useEffect(() => () => controller.current?.abort(), [])

  if (info.isPending) return <p className="muted">Checking the AI…</p>
  if (info.isError) return <ErrorMessage error={info.error} />
  if (info.data.status !== 'ready') {
    return <NotReady info={info.data} onRetry={() => info.refetch()} retrying={info.isFetching} />
  }

  const empty = content.trim() === ''
  const tooLong = content.length > info.data.max_chars

  function change(next: string) {
    setUndo(content)
    onChange(next)
  }

  async function run(action: Action) {
    controller.current?.abort()
    const mine = new AbortController()
    controller.current = mine
    setBusy(action)
    setError(null)
    setCopied(false)
    const post = { title, content }
    try {
      if (action === 'grammar') {
        setResult(null)
        const { fixes } = await aiApi.grammar(post)
        if (!mine.signal.aborted) setResult({ kind: 'grammar', fixes })
      } else {
        const start = { kind: 'text', action, basedOn: content } as const
        setResult({ ...start, text: '', done: false })
        const text = await aiApi.write(
          action,
          post,
          (soFar) => setResult({ ...start, text: soFar, done: false }),
          mine.signal,
        )
        setResult({ ...start, text, done: true })
      }
    } catch (caught) {
      // Stopped on purpose: keep what was written so far
      if (mine.signal.aborted) setResult((r) => (r?.kind === 'text' ? { ...r, done: true } : r))
      else setError(caught)
    } finally {
      if (controller.current === mine) {
        controller.current = null
        setBusy(null)
      }
    }
  }

  function stop() {
    controller.current?.abort()
  }

  function dropFix(fix: GrammarFix) {
    setResult((r) =>
      r?.kind === 'grammar' ? { ...r, fixes: r.fixes.filter((f) => f !== fix) } : r,
    )
  }

  function acceptFix(fix: GrammarFix) {
    // A function as the replacement, so "$" in the fix is taken literally
    change(content.replace(fix.original, () => fix.fix))
    dropFix(fix)
  }

  function acceptAll(fixes: GrammarFix[]) {
    let next = content
    for (const fix of fixes) next = next.replace(fix.original, () => fix.fix)
    change(next)
    setResult({ kind: 'grammar', fixes: [] })
  }

  async function copy(text: string) {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
    } catch {
      setError(new Error("Couldn't copy: your browser blocked the clipboard."))
    }
  }

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <h2 className={styles.title}>
          <Icon name="sparkles" size={18} /> AI assistant
        </h2>
        <p className={`muted ${styles.note}`}>
          {info.data.provider === 'claude'
            ? `Uses Claude (${info.data.model}): your post is sent to Anthropic to get suggestions.`
            : `Free, with ${info.data.model} on Lumen's own server: your post isn't sent to any outside AI service.`}{' '}
          Suggestions only: nothing changes until you accept it.
        </p>
      </div>

      <div className={styles.actions}>
        {ACTIONS.map((action) => (
          <button
            key={action.id}
            type="button"
            className={styles.action}
            aria-pressed={busy === action.id}
            disabled={empty || tooLong || busy !== null}
            onClick={() => run(action.id)}
          >
            <span className={styles.actionLabel}>{action.label}</span>
            <span className={styles.actionHint}>{action.hint}</span>
          </button>
        ))}
      </div>
      {empty && <p className="muted">Write something first, then ask the AI.</p>}
      {tooLong && (
        <p className="muted">
          This post is longer than the AI can read at once ({info.data.max_chars.toLocaleString()}{' '}
          characters).
        </p>
      )}

      {undo !== null && (
        <div className={styles.undo} role="status">
          Your text was changed by the AI.
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => {
              onChange(undo)
              setUndo(null)
            }}
          >
            Undo
          </button>
        </div>
      )}

      {busy && (
        <div className={styles.working} role="status">
          <span className={styles.spinner} aria-hidden />
          <span>
            {busy === 'grammar' ? 'Checking…' : 'Writing…'}{' '}
            <span className="muted">The first answer can take a minute while the model loads.</span>
          </span>
          {busy !== 'grammar' && (
            <button type="button" className="btn btn-ghost" onClick={stop}>
              Stop
            </button>
          )}
        </div>
      )}

      {error !== null && <ErrorMessage error={error} />}

      {result?.kind === 'grammar' && (
        <Fixes
          fixes={result.fixes}
          content={content}
          onAccept={acceptFix}
          onIgnore={dropFix}
          onAcceptAll={acceptAll}
        />
      )}

      {result?.kind === 'text' && (result.text || result.done) && (
        <section className={styles.result} aria-label={HEADINGS[result.action]}>
          <h3 className={styles.resultTitle}>{HEADINGS[result.action]}</h3>
          <div className={styles.answer} aria-busy={!result.done}>
            <Markdown>{result.text || '*No answer. Try again.*'}</Markdown>
          </div>
          {result.done && result.text && (
            <div className={styles.resultActions}>
              {result.action === 'polish' && (
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => {
                    change(result.text.trim())
                    setResult(null)
                  }}
                >
                  Use this version
                </button>
              )}
              <button type="button" className="btn btn-outline" onClick={() => copy(result.text)}>
                <Icon name="copy" size={16} /> {copied ? 'Copied' : 'Copy'}
              </button>
              <button type="button" className="btn btn-ghost" onClick={() => setResult(null)}>
                Dismiss
              </button>
            </div>
          )}
          {result.done && result.action === 'polish' && result.basedOn !== content && (
            <p className={`muted ${styles.note}`}>
              You've edited the post since this was written. Using it replaces those edits too.
            </p>
          )}
        </section>
      )}
    </div>
  )
}

interface FixesProps {
  fixes: GrammarFix[]
  content: string
  onAccept: (fix: GrammarFix) => void
  onIgnore: (fix: GrammarFix) => void
  onAcceptAll: (fixes: GrammarFix[]) => void
}

function Fixes({ fixes, content, onAccept, onIgnore, onAcceptAll }: FixesProps) {
  if (fixes.length === 0) {
    return <p className={styles.clean}>No mistakes left to fix. ✓</p>
  }
  // Words the author has since edited away can't be fixed any more
  const applicable = fixes.filter((fix) => content.includes(fix.original))

  return (
    <section className={styles.result} aria-label="Grammar fixes">
      <div className={styles.fixesHeader}>
        <h3 className={styles.resultTitle}>
          {fixes.length} {fixes.length === 1 ? 'fix' : 'fixes'}
        </h3>
        {applicable.length > 1 && (
          <button type="button" className="btn btn-outline" onClick={() => onAcceptAll(applicable)}>
            Accept all
          </button>
        )}
      </div>
      <ul className={styles.fixes}>
        {fixes.map((fix) => {
          const found = applicable.includes(fix)
          return (
            <li key={fix.original} className={styles.fix}>
              <p className={styles.change}>
                <del>{fix.original}</del> <span aria-hidden>→</span> <ins>{fix.fix}</ins>
              </p>
              <p className={`muted ${styles.reason}`}>
                {found ? fix.reason : 'No longer in your post.'}
              </p>
              <div className={styles.fixActions}>
                <button
                  type="button"
                  className="btn btn-primary"
                  disabled={!found}
                  onClick={() => onAccept(fix)}
                >
                  Accept
                </button>
                <button type="button" className="btn btn-ghost" onClick={() => onIgnore(fix)}>
                  Ignore
                </button>
              </div>
            </li>
          )
        })}
      </ul>
    </section>
  )
}

/** What to do when the model can't answer yet: set-up steps, then a retry */
function NotReady({
  info,
  onRetry,
  retrying,
}: {
  info: AiInfo
  onRetry: () => void
  retrying: boolean
}) {
  if (info.status === 'off') {
    return <p className="muted">AI writing help is turned off on this server.</p>
  }
  if (info.provider === 'claude') {
    return (
      <div className={styles.setup}>
        <h2 className={styles.title}>
          <Icon name="sparkles" size={18} /> Set up Claude
        </h2>
        <ClaudeSetup status={info.status} model={info.model} />
        <RetryButton onRetry={onRetry} retrying={retrying} />
      </div>
    )
  }
  return (
    <div className={styles.setup}>
      <h2 className={styles.title}>
        <Icon name="sparkles" size={18} /> Set up the free AI
      </h2>
      {info.status === 'not_running' ? (
        <ol>
          <li>
            Install Ollama from{' '}
            <a href="https://ollama.com/download" target="_blank" rel="noopener noreferrer">
              ollama.com
            </a>{' '}
            and open it.
          </li>
          <li>
            In a terminal, download the model once: <code>ollama pull {info.model}</code>
          </li>
        </ol>
      ) : (
        <p>
          Ollama is running, but the model isn't downloaded yet. In a terminal, run{' '}
          <code>ollama pull {info.model}</code> (a few GB, once).
        </p>
      )}
      <RetryButton onRetry={onRetry} retrying={retrying} />
    </div>
  )
}

function ClaudeSetup({ status, model }: { status: AiInfo['status']; model: string }) {
  if (status === 'model_missing') {
    return (
      <p>
        Claude has no model called <code>{model}</code>. Check <code>AI_MODEL</code> in{' '}
        <code>.env</code>.
      </p>
    )
  }
  if (status === 'not_running') {
    return <p>Couldn't reach the Claude API. Check the server's internet connection.</p>
  }
  return (
    <ol>
      <li>
        Create an API key at{' '}
        <a
          href="https://console.anthropic.com/settings/keys"
          target="_blank"
          rel="noopener noreferrer"
        >
          console.anthropic.com
        </a>
        .
      </li>
      <li>
        Add it to <code>.env</code> as <code>ANTHROPIC_API_KEY=…</code>, then restart the API.
      </li>
    </ol>
  )
}

function RetryButton({ onRetry, retrying }: { onRetry: () => void; retrying: boolean }) {
  return (
    <button type="button" className="btn btn-outline" onClick={onRetry} disabled={retrying}>
      {retrying ? 'Checking…' : 'Check again'}
    </button>
  )
}
