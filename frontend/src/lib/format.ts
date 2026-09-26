const dateFormat = new Intl.DateTimeFormat(undefined, {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
})

/** "26 Sept 2026", in the reader's own locale */
export function formatDate(iso: string): string {
  return dateFormat.format(new Date(iso))
}

const dateTimeFormat = new Intl.DateTimeFormat(undefined, {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
  hour: 'numeric',
  minute: '2-digit',
})

/** "26 Sept 2026, 7:57 pm", in the reader's own locale */
export function formatDateTime(iso: string): string {
  return dateTimeFormat.format(new Date(iso))
}

/** "1 comment", "3 comments" */
export function plural(count: number, word: string): string {
  return `${count} ${word}${count === 1 ? '' : 's'}`
}
