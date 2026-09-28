/**
 * How easy a post is to read, worked out in the browser: nothing is sent anywhere.
 *
 * Uses the Flesch reading-ease score: 0–100, higher is easier. Short sentences and
 * short words score high. It's made for English, so other languages score oddly.
 */

export type Level = 'easy' | 'fairly-easy' | 'medium' | 'hard'

export interface Sentence {
  text: string
  offset: number
  words: number
}

export interface Readability {
  score: number
  level: Level
  label: string
  words: number
  sentences: number
  averageWords: number
  minutes: number
  /** Sentences long enough to be worth splitting */
  long: Sentence[]
}

export const LONG_SENTENCE = 25
const WORDS_PER_MINUTE = 200

const WORD = /[\p{L}\p{N}]+(?:['’-][\p{L}\p{N}]+)*/gu
// A run of text up to and including its end marks, or up to a line break
const SENTENCE = /[^.!?\n]+(?:[.!?]+["'”’)\]]*|(?=\n)|$)/g

export function countWords(text: string): number {
  return text.match(WORD)?.length ?? 0
}

export function splitSentences(text: string): Sentence[] {
  const sentences: Sentence[] = []
  for (const match of text.matchAll(SENTENCE)) {
    const raw = match[0]
    const lead = raw.length - raw.trimStart().length
    const value = raw.trim()
    const words = countWords(value)
    if (words > 0) sentences.push({ text: value, offset: match.index + lead, words })
  }
  return sentences
}

/** A close guess for English: counts groups of vowels, minus a silent final e (or -ed, -es) */
export function syllables(word: string): number {
  const w = word.toLowerCase().replace(/[^a-z]/g, '')
  if (w.length === 0) return 0
  if (w.length <= 3) return 1
  const trimmed = w
    .replace(/(?:[^laeiouydt]es|[^laeiouydt]ed|[^laeiouy]e)$/, (end) => end[0])
    .replace(/^y/, '')
  return Math.max(1, trimmed.match(/[aeiouy]+/g)?.length ?? 1)
}

function levelOf(score: number): { level: Level; label: string } {
  if (score >= 70) return { level: 'easy', label: 'Easy to read' }
  if (score >= 60) return { level: 'fairly-easy', label: 'Fairly easy' }
  if (score >= 50) return { level: 'medium', label: 'Medium' }
  return { level: 'hard', label: 'Hard to read' }
}

export function readability(text: string): Readability | null {
  const sentences = splitSentences(text)
  const words = text.match(WORD) ?? []
  if (words.length === 0 || sentences.length === 0) return null

  const syllableCount = words.reduce((sum, word) => sum + syllables(word), 0)
  const averageWords = words.length / sentences.length
  const raw = 206.835 - 1.015 * averageWords - 84.6 * (syllableCount / words.length)
  const score = Math.round(Math.min(100, Math.max(0, raw)))

  return {
    score,
    ...levelOf(score),
    words: words.length,
    sentences: sentences.length,
    averageWords: Math.round(averageWords * 10) / 10,
    minutes: Math.max(1, Math.round(words.length / WORDS_PER_MINUTE)),
    long: sentences.filter((s) => s.words > LONG_SENTENCE),
  }
}
