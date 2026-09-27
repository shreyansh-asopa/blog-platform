import { useState } from 'react'
import type { FormEvent } from 'react'
import { Icon } from './Icon'
import styles from './SearchForm.module.css'

interface Props {
  /** What the box starts with, e.g. the URL's current ?q= */
  initial?: string
  placeholder?: string
  onSearch: (q: string) => void
  autoFocus?: boolean
  /** Lets two instances share a page without a duplicate id */
  id?: string
}

/** A rounded search box: icon, text field and submit button. Used on /search and the home page. */
export function SearchForm({
  initial = '',
  placeholder = 'Search posts…',
  onSearch,
  autoFocus,
  id = 'search-box',
}: Props) {
  // What's in the box; the caller decides what happens (a new URL, a navigation) on submit
  const [typed, setTyped] = useState(initial)

  function submit(event: FormEvent) {
    event.preventDefault()
    onSearch(typed.trim())
  }

  return (
    <form role="search" className={styles.form} onSubmit={submit}>
      <label htmlFor={id} className="visually-hidden">
        Search posts
      </label>
      <Icon name="search" />
      <input
        id={id}
        type="search"
        className={styles.input}
        placeholder={placeholder}
        value={typed}
        onChange={(event) => setTyped(event.target.value)}
        maxLength={200}
        autoFocus={autoFocus}
      />
      <button type="submit" className="btn btn-primary">
        Search
      </button>
    </form>
  )
}
