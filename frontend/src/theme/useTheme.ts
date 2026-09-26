import { useCallback, useState } from 'react'

/** "system" follows the OS setting; the other two override it */
export type ThemeChoice = 'system' | 'light' | 'dark'

const KEY = 'lumen-theme'
const ORDER: ThemeChoice[] = ['system', 'light', 'dark']

function read(): ThemeChoice {
  try {
    const saved = localStorage.getItem(KEY)
    return saved === 'light' || saved === 'dark' ? saved : 'system'
  } catch {
    return 'system'
  }
}

function apply(choice: ThemeChoice) {
  // global.css picks colours from this attribute, or from the OS when it is absent
  if (choice === 'system') delete document.documentElement.dataset.theme
  else document.documentElement.dataset.theme = choice
  try {
    if (choice === 'system') localStorage.removeItem(KEY)
    else localStorage.setItem(KEY, choice)
  } catch {
    // Not remembered across visits, but still applied now
  }
}

export function useTheme() {
  const [choice, setChoice] = useState(read)

  const cycle = useCallback(() => {
    const next = ORDER[(ORDER.indexOf(choice) + 1) % ORDER.length]
    apply(next)
    setChoice(next)
  }, [choice])

  return { choice, cycle }
}
