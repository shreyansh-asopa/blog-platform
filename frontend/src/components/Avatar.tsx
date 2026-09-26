import type { CSSProperties } from 'react'
import styles from './Avatar.module.css'

// The same name always gets the same colour, so people are recognisable at a glance
const HUES = [230, 262, 199, 160, 25, 340, 45, 290]

function hueFor(name: string): number {
  let hash = 0
  for (const char of name) hash = (hash * 31 + char.charCodeAt(0)) | 0
  return HUES[Math.abs(hash) % HUES.length]
}

export function Avatar({ name, size = 32 }: { name: string; size?: number }) {
  return (
    <span
      className={styles.avatar}
      style={
        { width: size, height: size, fontSize: size * 0.45, '--hue': hueFor(name) } as CSSProperties
      }
      aria-hidden
    >
      {name.charAt(0).toUpperCase()}
    </span>
  )
}
