import { EditorContent, useEditor, useEditorState, type Editor } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import { TableKit } from '@tiptap/extension-table'
import TextAlign from '@tiptap/extension-text-align'
import { Color, FontFamily, FontSize, TextStyle } from '@tiptap/extension-text-style'
import { Placeholder } from '@tiptap/extensions'
import { useEffect, useImperativeHandle, useRef, useState } from 'react'
import type { ReactNode, Ref } from 'react'
import { Icon, type IconName } from './Icon'
import prose from './Markdown.module.css'
import { CheckBar } from './writing/CheckBar'
import styles from './RichEditor.module.css'

// Fixed choices keep posts consistent. The browser reports colours as rgb(), so they're
// written that way too: then the toolbar can tell which one the cursor is in.
const FONTS = [
  { label: 'Sans', value: '' },
  { label: 'Serif', value: 'ui-serif, Georgia, serif' },
  { label: 'Mono', value: 'ui-monospace, Menlo, monospace' },
]
const SIZES = [
  { label: 'Small', value: '14px' },
  { label: 'Normal', value: '' },
  { label: 'Large', value: '22px' },
  { label: 'Extra large', value: '28px' },
]
// Mid-tones that keep enough contrast on both the light and the dark background
const COLORS = [
  { label: 'Red', value: 'rgb(239, 68, 68)' },
  { label: 'Orange', value: 'rgb(234, 88, 12)' },
  { label: 'Amber', value: 'rgb(217, 119, 6)' },
  { label: 'Green', value: 'rgb(22, 163, 74)' },
  { label: 'Teal', value: 'rgb(13, 148, 136)' },
  { label: 'Blue', value: 'rgb(59, 130, 246)' },
  { label: 'Violet', value: 'rgb(139, 92, 246)' },
  { label: 'Pink', value: 'rgb(236, 72, 153)' },
]
const ALIGNS = [
  { value: 'left', label: 'Align left', icon: 'alignLeft' },
  { value: 'center', label: 'Centre', icon: 'alignCenter' },
  { value: 'right', label: 'Align right', icon: 'alignRight' },
  { value: 'justify', label: 'Justify', icon: 'alignJustify' },
] as const

export interface RichEditorHandle {
  focus: () => void
}

interface Props {
  id: string
  /** Read once, when the editor starts */
  initialHtml: string
  placeholder: string
  /** html is '' when the editor is empty; text is the words alone, without tags */
  onChange: (html: string, text: string) => void
  ref?: Ref<RichEditorHandle>
}

/** A Word-like editor: a formatting toolbar above a writing area that shows the formatting */
export function RichEditor({ id, initialHtml, placeholder, onChange, ref }: Props) {
  // Tiptap keeps the first callback it was given, so it reads the latest one through a ref
  const changed = useRef(onChange)
  useEffect(() => {
    changed.current = onChange
  })

  const report = (editor: Editor) => {
    // React's development mode mounts twice, and can hand over an editor tiptap has already
    // torn down: its schema is gone even while isDestroyed still reads false
    if (editor.isDestroyed || !(editor.schema as Editor['schema'] | null)) return
    changed.current(editor.isEmpty ? '' : editor.getHTML(), editor.getText())
  }

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: { levels: [2, 3] },
        link: { openOnClick: false, autolink: true, defaultProtocol: 'https' },
      }),
      TextStyle,
      Color,
      FontFamily,
      FontSize,
      TextAlign.configure({ types: ['heading', 'paragraph'] }),
      TableKit.configure({ table: { resizable: false } }),
      Placeholder.configure({ placeholder }),
    ],
    content: initialHtml,
    editorProps: {
      attributes: {
        id,
        class: `${prose.prose} ${styles.content}`,
        role: 'textbox',
        'aria-multiline': 'true',
        'aria-label': 'Post content',
        spellcheck: 'true',
      },
    },
    onUpdate: ({ editor }) => report(editor),
  })

  // The first report is what the editor loaded. Tiptap's onCreate option can fire before this
  // component is on screen, when React won't take state updates yet, so it's done here:
  // at once if the editor is ready, or as soon as it is.
  useEffect(() => {
    if (editor.isInitialized) {
      report(editor)
      return
    }
    const ready = () => report(editor)
    editor.on('create', ready)
    return () => {
      editor.off('create', ready)
    }
  }, [editor])

  useImperativeHandle(ref, () => ({ focus: () => editor.commands.focus('start') }), [editor])

  return (
    <div className={styles.editor}>
      <Toolbar editor={editor} controls={id} />
      <CheckBar editor={editor} />
      <EditorContent editor={editor} />
    </div>
  )
}

function Toolbar({ editor, controls }: { editor: Editor; controls: string }) {
  // Re-renders the toolbar only when what it shows changes, not on every keystroke
  const state = useEditorState({
    editor,
    selector: ({ editor }) => {
      const style = editor.getAttributes('textStyle')
      return {
        block: editor.isActive('heading', { level: 2 })
          ? 'h2'
          : editor.isActive('heading', { level: 3 })
            ? 'h3'
            : 'p',
        font: (style.fontFamily as string | undefined) ?? '',
        size: (style.fontSize as string | undefined) ?? '',
        color: (style.color as string | undefined) ?? '',
        bold: editor.isActive('bold'),
        italic: editor.isActive('italic'),
        underline: editor.isActive('underline'),
        strike: editor.isActive('strike'),
        align: ALIGNS.find((a) => editor.isActive({ textAlign: a.value }))?.value ?? 'left',
        bulletList: editor.isActive('bulletList'),
        orderedList: editor.isActive('orderedList'),
        blockquote: editor.isActive('blockquote'),
        codeBlock: editor.isActive('codeBlock'),
        link: editor.isActive('link'),
        canUndo: editor.can().undo(),
        canRedo: editor.can().redo(),
      }
    },
  })
  const chain = () => editor.chain().focus()

  function setLink() {
    const current = editor.getAttributes('link').href as string | undefined
    const answer = window.prompt(
      'Link address (leave empty to remove the link)',
      current ?? 'https://',
    )
    if (answer === null) return
    const url = answer.trim()
    if (url === '' || url === 'https://') {
      chain().extendMarkRange('link').unsetLink().run()
      return
    }
    const href = /^(https?:|mailto:)/i.test(url) ? url : `https://${url}`
    chain().extendMarkRange('link').setLink({ href }).run()
  }

  return (
    <div className={styles.toolbar} role="toolbar" aria-label="Formatting" aria-controls={controls}>
      <div className={styles.group}>
        <select
          className={styles.select}
          aria-label="Text style"
          title="Text style"
          value={state.block}
          onChange={(event) => {
            const block = event.target.value
            if (block === 'p') chain().setParagraph().run()
            else
              chain()
                .setHeading({ level: block === 'h2' ? 2 : 3 })
                .run()
          }}
        >
          <option value="p">Paragraph</option>
          <option value="h2">Heading</option>
          <option value="h3">Subheading</option>
        </select>
        <select
          className={styles.select}
          aria-label="Font"
          title="Font"
          value={state.font}
          onChange={(event) => {
            const font = event.target.value
            if (font) chain().setFontFamily(font).run()
            else chain().unsetFontFamily().run()
          }}
        >
          {FONTS.map((font) => (
            <option key={font.label} value={font.value}>
              {font.label}
            </option>
          ))}
        </select>
        <select
          className={styles.select}
          aria-label="Font size"
          title="Font size"
          value={state.size}
          onChange={(event) => {
            const size = event.target.value
            if (size) chain().setFontSize(size).run()
            else chain().unsetFontSize().run()
          }}
        >
          {SIZES.map((size) => (
            <option key={size.label} value={size.value}>
              {size.label}
            </option>
          ))}
        </select>
      </div>

      <div className={styles.group}>
        <Tool label="Bold (⌘B)" active={state.bold} onClick={() => chain().toggleBold().run()}>
          <b>B</b>
        </Tool>
        <Tool
          label="Italic (⌘I)"
          active={state.italic}
          onClick={() => chain().toggleItalic().run()}
        >
          <i>I</i>
        </Tool>
        <Tool
          label="Underline (⌘U)"
          active={state.underline}
          onClick={() => chain().toggleUnderline().run()}
        >
          <u>U</u>
        </Tool>
        <Tool
          label="Strikethrough"
          active={state.strike}
          onClick={() => chain().toggleStrike().run()}
        >
          <s>S</s>
        </Tool>
        <ColorPicker
          color={state.color}
          onPick={(color) => (color ? chain().setColor(color).run() : chain().unsetColor().run())}
        />
      </div>

      <div className={styles.group}>
        {ALIGNS.map((align) => (
          <Tool
            key={align.value}
            label={align.label}
            icon={align.icon}
            active={state.align === align.value}
            onClick={() => chain().setTextAlign(align.value).run()}
          />
        ))}
      </div>

      <div className={styles.group}>
        <Tool
          label="Bullet list"
          icon="listBullet"
          active={state.bulletList}
          onClick={() => chain().toggleBulletList().run()}
        />
        <Tool
          label="Numbered list"
          icon="listNumbered"
          active={state.orderedList}
          onClick={() => chain().toggleOrderedList().run()}
        />
        <Tool
          label="Quote"
          icon="quote"
          active={state.blockquote}
          onClick={() => chain().toggleBlockquote().run()}
        />
        <Tool
          label="Code block"
          icon="code"
          active={state.codeBlock}
          onClick={() => chain().toggleCodeBlock().run()}
        />
        <Tool label="Link" icon="link" active={state.link} onClick={setLink} />
      </div>

      <div className={styles.group}>
        <Tool
          label="Undo (⌘Z)"
          icon="undo"
          disabled={!state.canUndo}
          onClick={() => chain().undo().run()}
        />
        <Tool
          label="Redo (⌘⇧Z)"
          icon="redo"
          disabled={!state.canRedo}
          onClick={() => chain().redo().run()}
        />
        <Tool
          label="Clear formatting"
          icon="clearFormat"
          onClick={() => chain().unsetAllMarks().clearNodes().unsetTextAlign().run()}
        />
      </div>
    </div>
  )
}

interface ToolProps {
  label: string
  icon?: IconName
  /** Left out for one-off actions like undo, which have no on/off state */
  active?: boolean
  disabled?: boolean
  onClick: () => void
  children?: ReactNode
}

function Tool({ label, icon, active, disabled, onClick, children }: ToolProps) {
  return (
    <button
      type="button"
      className={styles.tool}
      aria-label={label}
      title={label}
      aria-pressed={active}
      disabled={disabled}
      // Keeps the text selected: a normal click would move focus off the writing area
      onMouseDown={(event) => event.preventDefault()}
      onClick={onClick}
    >
      {icon ? <Icon name={icon} size={18} /> : children}
    </button>
  )
}

/** An "A" underlined in the current colour; opens a small palette */
function ColorPicker({ color, onPick }: { color: string; onPick: (color: string) => void }) {
  const [open, setOpen] = useState(false)
  const root = useRef<HTMLDivElement>(null)

  // Closes on a click anywhere else, or Escape
  useEffect(() => {
    if (!open) return
    const onDown = (event: MouseEvent) => {
      if (!root.current?.contains(event.target as Node)) setOpen(false)
    }
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', onDown)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDown)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  const pick = (value: string) => {
    onPick(value)
    setOpen(false)
  }

  return (
    <div className={styles.colorPicker} ref={root}>
      <button
        type="button"
        className={styles.tool}
        aria-label="Text colour"
        title="Text colour"
        aria-expanded={open}
        aria-haspopup="true"
        onMouseDown={(event) => event.preventDefault()}
        onClick={() => setOpen(!open)}
      >
        <span className={styles.colorA} style={{ borderColor: color || 'currentColor' }}>
          A
        </span>
      </button>
      {open && (
        <div className={styles.palette} role="group" aria-label="Text colours">
          <button
            type="button"
            className={styles.defaultColor}
            aria-pressed={color === ''}
            onMouseDown={(event) => event.preventDefault()}
            onClick={() => pick('')}
          >
            Default
          </button>
          <div className={styles.swatches}>
            {COLORS.map((c) => (
              <button
                key={c.label}
                type="button"
                className={styles.swatch}
                style={{ background: c.value }}
                aria-label={c.label}
                title={c.label}
                aria-pressed={color === c.value}
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => pick(c.value)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
