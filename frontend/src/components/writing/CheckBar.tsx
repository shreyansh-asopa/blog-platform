import { useEditorState, type Editor } from '@tiptap/react'
import { useRef, useState } from 'react'
import { useWritingStatus } from '../../api/useWriting'
import { readDoc, showTarget, type Target } from '../../lib/editorText'
import { Icon, type IconName } from '../Icon'
import { CheckDialog } from './CheckDialog'
import { GrammarPanel, type GrammarPanelHandle } from './GrammarPanel'
import { ReadabilityPanel } from './ReadabilityPanel'
import { TonePanel } from './TonePanel'
import styles from './Writing.module.css'

type Check = 'grammar' | 'readability' | 'tone'

const CHECKS: { check: Check; label: string; icon: IconName; hint: string }[] = [
  {
    check: 'grammar',
    label: 'Grammar',
    icon: 'check',
    hint: 'Spelling, grammar, punctuation and whole-sentence fixes',
  },
  {
    check: 'readability',
    label: 'Readability',
    icon: 'book',
    hint: 'How easy the post is to read',
  },
  { check: 'tone', label: 'Tone', icon: 'sparkle', hint: 'How the post sounds, with AI rewrites' },
]

// Until the status arrives, assume the usual limit and that the AI isn't there
const DEFAULT_MAX = 20_000

const AI_NAMES = { gemini: 'Google Gemini', groq: 'Groq' } as const

/**
 * "Check your writing": a strip of buttons under the formatting toolbar. Each opens a
 * popup; whatever is accepted there is an ordinary edit, so it shows in the post at once,
 * can be undone, and is saved with the post.
 */
export function CheckBar({ editor }: { editor: Editor }) {
  const status = useWritingStatus()
  const grammar = useRef<GrammarPanelHandle>(null)
  const [open, setOpen] = useState<Check | null>(null)
  const [badges, setBadges] = useState<Record<Check, string | null>>({
    grammar: null,
    readability: null,
    tone: null,
  })

  const state = useEditorState({
    editor,
    selector: ({ editor }) => ({ text: readDoc(editor).text, canUndo: editor.can().undo() }),
  })

  // Made once, so the panels' badge effects don't run again on every render
  const [onBadge] = useState(() => {
    const make = (check: Check) => (value: string | null) =>
      setBadges((all) => (all[check] === value ? all : { ...all, [check]: value }))
    return { grammar: make('grammar'), readability: make('readability'), tone: make('tone') }
  })

  const close = () => setOpen(null)
  const show = (target: Target) => {
    close()
    // After the popup is gone, so the selected words are what the writer sees
    requestAnimationFrame(() => showTarget(editor, target))
  }
  const undo = () => editor.commands.undo()

  const maxChars = status.data?.max_chars ?? DEFAULT_MAX
  const aiReady = status.data?.tone === 'ready'
  const aiName = status.data?.ai ? AI_NAMES[status.data.ai] : null
  const dialog = { canUndo: state.canUndo, onUndo: undo, onClose: close }

  return (
    <>
      <div className={styles.bar} role="group" aria-label="Check your writing">
        <span className={styles.barLabel}>Check your writing</span>
        {CHECKS.map(({ check, label, icon, hint }) => (
          <button
            key={check}
            type="button"
            className={styles.check}
            title={hint}
            aria-haspopup="dialog"
            aria-expanded={open === check}
            onClick={() => {
              setOpen(check)
              if (check === 'grammar') grammar.current?.opened()
            }}
          >
            <Icon name={icon} size={16} />
            {label}
            {badges[check] !== null && (
              <span className={styles.badge} data-good={badges[check] === '✓' || undefined}>
                {badges[check]}
              </span>
            )}
          </button>
        ))}
      </div>

      <CheckDialog
        open={open === 'grammar'}
        title="Grammar"
        subtitle="Whole sentences, spelling, grammar, punctuation and style"
        privacy={`Your text is sent to LanguageTool${aiName ? ` and ${aiName}` : ''} to check it.`}
        {...dialog}
      >
        <GrammarPanel
          editor={editor}
          text={state.text}
          ref={grammar}
          maxChars={maxChars}
          aiName={aiName}
          onBadge={onBadge.grammar}
          onShow={show}
        />
      </CheckDialog>

      <CheckDialog
        open={open === 'readability'}
        title="Readability"
        subtitle="Updates as you type"
        privacy={`Worked out in your browser. Only “Simplify with AI” sends a sentence to ${aiName ?? 'the AI'}.`}
        {...dialog}
      >
        <ReadabilityPanel
          editor={editor}
          text={state.text}
          aiReady={aiReady}
          onBadge={onBadge.readability}
          onShow={show}
        />
      </CheckDialog>

      <CheckDialog
        open={open === 'tone'}
        title="Tone"
        subtitle="How your post sounds, and rewrites to match what you want"
        privacy={`Your text is sent to ${aiName ?? 'the AI'} to check it.`}
        {...dialog}
      >
        <TonePanel
          editor={editor}
          text={state.text}
          ready={aiReady}
          maxChars={maxChars}
          onBadge={onBadge.tone}
          onShow={show}
        />
      </CheckDialog>
    </>
  )
}
