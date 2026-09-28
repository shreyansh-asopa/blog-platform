import type { Editor } from '@tiptap/react'

/**
 * The post as plain text, the way the writing checks read it, plus where each character
 * sits in the editor's document. Checks answer with positions in the plain text; this
 * map turns them back into places in the formatted post, so a fix lands on the right
 * words and keeps their bold, colour and so on.
 */
export interface DocText {
  text: string
  /** Document position of each character in `text`; -1 for the gaps between blocks */
  positions: number[]
}

/** Paragraphs and headings are separated by a blank line. Code blocks are left out */
export function readDoc(editor: Editor): DocText {
  let text = ''
  const positions: number[] = []
  let started = false

  const gap = (value: string) => {
    text += value
    for (let i = 0; i < value.length; i++) positions.push(-1)
  }

  editor.state.doc.descendants((node, pos) => {
    if (node.type.name === 'codeBlock') {
      if (started) gap('\n\n')
      started = true
      return false
    }
    if (node.isTextblock) {
      if (started) gap('\n\n')
      started = true
      return true
    }
    if (node.isText) {
      const value = node.text ?? ''
      text += value
      // One document position per UTF-16 unit, the same unit JavaScript strings count in
      for (let i = 0; i < value.length; i++) positions.push(pos + i)
      return false
    }
    if (node.type.name === 'hardBreak') {
      gap('\n')
      return false
    }
    return true
  })
  return { text, positions }
}

/** Some words in the post, remembered well enough to find them again after edits */
export interface Target {
  original: string
  offset: number
  before: string
  after: string
}

const CONTEXT = 24

export function targetAt(text: string, offset: number, length: number): Target {
  return {
    original: text.slice(offset, offset + length),
    offset,
    before: text.slice(Math.max(0, offset - CONTEXT), offset),
    after: text.slice(offset + length, offset + length + CONTEXT),
  }
}

/** A target for words known only by their text, like a sentence the AI rewrote */
export function targetFor(text: string, original: string): Target | null {
  const offset = text.indexOf(original)
  return offset === -1 ? null : targetAt(text, offset, original.length)
}

export interface Range {
  from: number
  to: number
}

/**
 * Where the target's words are now. Earlier fixes shift everything after them, so the
 * words are looked for again: first with the text around them, then the nearest match.
 * Null when they're gone, for example because the writer changed them.
 */
export function findTarget(doc: DocText, target: Target): Range | null {
  const { text, positions } = doc
  const { original, offset, before, after } = target
  if (original === '') return null

  let best: { index: number; score: number } | null = null
  for (
    let index = text.indexOf(original);
    index !== -1;
    index = text.indexOf(original, index + 1)
  ) {
    const end = index + original.length
    // Can't span two paragraphs
    if (positions.slice(index, end).some((p) => p === -1)) continue
    const context =
      Number(text.slice(index - before.length, index) === before) +
      Number(text.slice(end, end + after.length) === after)
    // Matching context matters most; distance from where it was breaks ties
    const score = context * 1_000_000 - Math.abs(index - offset)
    if (!best || score > best.score) best = { index, score }
  }
  if (!best) return null
  return {
    from: positions[best.index],
    to: positions[best.index + original.length - 1] + 1,
  }
}

/**
 * Swaps the target's words for `replacement` as a normal edit, so it can be undone and
 * counts as an unsaved change. Returns false when the words can't be found any more.
 */
export function replaceTarget(editor: Editor, target: Target, replacement: string): boolean {
  const range = findTarget(readDoc(editor), target)
  if (!range) return false
  editor
    .chain()
    // insertText keeps the formatting of the words it replaces
    .command(({ tr }) => {
      tr.insertText(replacement, range.from, range.to)
      return true
    })
    .run()
  return true
}

/** Closes nothing itself: callers close their popup first, so the selection is visible */
export function showTarget(editor: Editor, target: Target): boolean {
  const range = findTarget(readDoc(editor), target)
  if (!range) return false
  editor.chain().focus().setTextSelection(range).scrollIntoView().run()
  return true
}
