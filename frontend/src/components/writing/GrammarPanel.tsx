import type { Editor } from '@tiptap/react'
import { useEffect, useImperativeHandle, useState } from 'react'
import type { Ref } from 'react'
import { writingApi } from '../../api/endpoints'
import type { GrammarIssue, IssueCategory, Suggestion } from '../../api/types'
import { readDoc, replaceTarget, targetAt, targetFor, type Target } from '../../lib/editorText'
import { plural } from '../../lib/format'
import { countWords } from '../../lib/readability'
import { ErrorMessage } from '../ErrorMessage'
import { Icon } from '../Icon'
import { Spinner, StaleNotice } from './CheckDialog'
import styles from './Writing.module.css'

const GROUPS: { category: IssueCategory; label: string }[] = [
  { category: 'spelling', label: 'Spelling' },
  { category: 'grammar', label: 'Grammar' },
  { category: 'punctuation', label: 'Punctuation' },
  { category: 'style', label: 'Style' },
]

interface Issue extends GrammarIssue {
  id: string
  target: Target
  /** Fixed, ignored, or its words were changed by hand, so it's no longer shown */
  done: boolean
}

/** A whole sentence the AI corrected */
interface SentenceFix extends Suggestion {
  id: string
  target: Target
  done: boolean
}

interface Result {
  issues: Issue[]
  sentences: SentenceFix[]
  note: string | null
}

interface Props {
  editor: Editor
  /** The post as the checks read it, kept up to date as the writer types */
  text: string
  maxChars: number
  /** The AI's name when it's set up; without it only single words are checked */
  aiName: string | null
  onBadge: (badge: string | null) => void
  onShow: (target: Target) => void
  ref?: Ref<GrammarPanelHandle>
}

export interface GrammarPanelHandle {
  /** Called as the popup opens: checks by itself the first time */
  opened: () => void
}

const covers = (sentence: SentenceFix, issue: Issue) =>
  sentence.target.offset <= issue.target.offset &&
  issue.target.offset < sentence.target.offset + sentence.target.original.length

export function GrammarPanel({ editor, text, maxChars, aiName, onBadge, onShow, ref }: Props) {
  const [result, setResult] = useState<Result | null>(null)
  // The post as it should read if only this panel changed it: typing makes the check stale
  const [expected, setExpected] = useState('')
  const [checking, setChecking] = useState(false)
  const [error, setError] = useState<unknown>(null)

  const empty = text.trim() === ''
  const tooLong = text.length > maxChars

  async function check() {
    const sent = readDoc(editor).text
    if (sent.trim() === '' || sent.length > maxChars) return
    setChecking(true)
    setError(null)
    try {
      const answer = await writingApi.grammar(sent)
      setResult({
        issues: answer.issues.map((issue, i) => ({
          ...issue,
          id: `w${i}`,
          target: targetAt(sent, issue.offset, issue.length),
          done: false,
        })),
        sentences: answer.sentences.flatMap((suggestion, i) => {
          const target = targetFor(sent, suggestion.original)
          return target ? [{ ...suggestion, id: `s${i}`, target, done: false }] : []
        }),
        note: answer.note,
      })
      setExpected(sent)
    } catch (caught) {
      setError(caught)
    } finally {
      setChecking(false)
    }
  }

  useImperativeHandle(ref, () => ({
    opened: () => {
      if (result === null && !checking && error === null) void check()
    },
  }))

  const sentences = result?.sentences.filter((s) => !s.done) ?? []
  // A word inside a sentence the AI rewrote is fixed by that rewrite, so it's only
  // shown again if the writer ignores the sentence
  const words = result?.issues.filter((i) => !i.done && !sentences.some((s) => covers(s, i))) ?? []
  const pending = sentences.length + words.length
  useEffect(() => {
    onBadge(result === null ? null : pending === 0 ? '✓' : String(pending))
  }, [result, pending, onBadge])

  /** `accepted` sentences were put in the post, which also fixes the word mistakes inside */
  const finish = (ids: string[], accepted: string[] = []) => {
    setResult((r) => {
      if (!r) return r
      const rewritten = r.sentences.filter((s) => accepted.includes(s.id))
      const settled = (i: Issue) => ids.includes(i.id) || rewritten.some((s) => covers(s, i))
      return {
        ...r,
        issues: r.issues.map((i) => (settled(i) ? { ...i, done: true } : i)),
        sentences: r.sentences.map((s) => (ids.includes(s.id) ? { ...s, done: true } : s)),
      }
    })
    setExpected(readDoc(editor).text)
  }

  function fixWord(issue: Issue, replacement: string) {
    // If the words can't be found they were edited by hand, so the card has nothing to do
    replaceTarget(editor, issue.target, replacement)
    finish([issue.id])
  }

  function fixSentence(sentence: SentenceFix) {
    replaceTarget(editor, sentence.target, sentence.fix)
    finish([sentence.id], [sentence.id])
  }

  const fixableWords = words.filter((issue) => issue.replacements.length > 0)
  const fixable = sentences.length + fixableWords.length

  function fixAll() {
    // From the end backwards, so each fix leaves the places of the earlier ones alone
    const fixes = [
      ...sentences.map((s) => ({ id: s.id, target: s.target, to: s.fix })),
      ...fixableWords.map((i) => ({ id: i.id, target: i.target, to: i.replacements[0] })),
    ].sort((a, b) => b.target.offset - a.target.offset)
    for (const fix of fixes) replaceTarget(editor, fix.target, fix.to)
    finish(
      fixes.map((fix) => fix.id),
      sentences.map((s) => s.id),
    )
  }

  if (empty) return <p className={styles.empty}>Write something first, then check it here.</p>
  if (tooLong)
    return (
      <p className={styles.empty}>
        The post is too long to check at once (the most is {maxChars.toLocaleString()} characters;
        this one has {text.length.toLocaleString()}).
      </p>
    )
  if (checking) return <Spinner label={`Checking ${countWords(text).toLocaleString()} words…`} />
  if (error)
    return (
      <div className={styles.stack}>
        <ErrorMessage error={error} />
        <button type="button" className="btn btn-outline" onClick={() => void check()}>
          Try again
        </button>
      </div>
    )
  if (result === null) return null

  const stale = text !== expected

  return (
    <div className={styles.stack}>
      {stale && <StaleNotice onRecheck={() => void check()} />}
      {result.note && (
        <p className={styles.note} role="status">
          {result.note}
        </p>
      )}
      {aiName === null && (
        <p className={styles.tip}>
          Only single words are checked. To also fix whole sentences (verb forms, tenses, word
          order), whoever runs this site can add a free AI key (<code>GEMINI_API_KEY</code> or{' '}
          <code>GROQ_API_KEY</code>) to the server's settings.
        </p>
      )}

      {pending === 0 ? (
        <p className={styles.empty}>
          <span className={styles.emptyIcon}>🎉</span>
          No problems found
        </p>
      ) : (
        <div className={styles.summary}>
          <span>{plural(pending, 'thing')} to look at</span>
          {fixable > 1 && (
            <button type="button" className="btn btn-primary" onClick={fixAll}>
              Fix all {fixable}
            </button>
          )}
        </div>
      )}

      {sentences.length > 0 && (
        <section className={styles.group} aria-label="Sentences">
          <h3 className={styles.groupTitle}>
            <span className={styles.dot} data-category="sentence" aria-hidden />
            Sentences <span className="muted">{sentences.length}</span>
          </h3>
          {sentences.map((sentence) => (
            <article key={sentence.id} className={styles.issue} data-category="sentence">
              <p className={styles.before}>
                <del>{sentence.original}</del>
              </p>
              <p className={styles.after}>{sentence.fix}</p>
              {sentence.reason && <p className={styles.message}>{sentence.reason}</p>}
              <div className={styles.actions}>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => fixSentence(sentence)}
                >
                  <Icon name="check" size={16} /> Accept
                </button>
                <span className={styles.spacer} />
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={() => onShow(sentence.target)}
                >
                  Show in post
                </button>
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={() => finish([sentence.id])}
                >
                  Ignore
                </button>
              </div>
            </article>
          ))}
        </section>
      )}

      {GROUPS.map(({ category, label }) => {
        const group = words.filter((issue) => issue.category === category)
        if (group.length === 0) return null
        return (
          <section key={category} className={styles.group} aria-label={label}>
            <h3 className={styles.groupTitle}>
              <span className={styles.dot} data-category={category} aria-hidden />
              {label} <span className="muted">{group.length}</span>
            </h3>
            {group.map((issue) => (
              <IssueCard
                key={issue.id}
                issue={issue}
                onFix={(replacement) => fixWord(issue, replacement)}
                onIgnore={() => finish([issue.id])}
                onShow={() => onShow(issue.target)}
              />
            ))}
          </section>
        )
      })}
    </div>
  )
}

interface CardProps {
  issue: Issue
  onFix: (replacement: string) => void
  onIgnore: () => void
  onShow: () => void
}

function IssueCard({ issue, onFix, onIgnore, onShow }: CardProps) {
  const { before, original, after } = issue.target
  // Only the words close by: the rest of the paragraph would bury the mistake
  const lead =
    before
      .split('\n')
      .at(-1)
      ?.replace(/^\S*\s/, '') ?? ''
  const tail = after.split('\n')[0].replace(/\s\S*$/, '')

  return (
    <article className={styles.issue} data-category={issue.category}>
      <p className={styles.context}>
        {lead !== before && '…'}
        {lead}
        <mark>{original.trim() === '' ? '␣' : original}</mark>
        {tail}
        {tail !== after && '…'}
      </p>
      <p className={styles.message}>{issue.message}</p>
      <div className={styles.actions}>
        {issue.replacements.map((replacement) => (
          <button
            key={replacement}
            type="button"
            className={styles.fix}
            title={`Change to “${replacement}”`}
            onClick={() => onFix(replacement)}
          >
            {replacement === '' ? 'Remove' : replacement.trim() === '' ? '␣ (space)' : replacement}
          </button>
        ))}
        <span className={styles.spacer} />
        <button type="button" className="btn btn-ghost" onClick={onShow}>
          Show in post
        </button>
        <button type="button" className="btn btn-ghost" onClick={onIgnore}>
          Ignore
        </button>
      </div>
    </article>
  )
}
