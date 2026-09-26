import { Link } from 'react-router'
import styles from './Hero.module.css'
import { Icon, type IconName } from './Icon'

const FEATURES: { icon: IconName; title: string; text: string }[] = [
  {
    icon: 'code',
    title: 'Built for technical writing',
    text: 'Markdown with code blocks, tables and quotes. Write in plain text, read it beautifully.',
  },
  {
    icon: 'moon',
    title: 'Easy on the eyes',
    text: 'Light and dark themes that follow your system, or pick one yourself.',
  },
  {
    icon: 'heart',
    title: 'Readers, not algorithms',
    text: 'A simple feed, newest first. Likes tell writers what landed.',
  },
  {
    icon: 'comment',
    title: 'Discussion that stays kind',
    text: 'Every comment is checked by moderation before it appears.',
  },
  {
    icon: 'draft',
    title: 'Drafts until you are ready',
    text: 'Nobody sees a post until you publish it. Unpublish any time.',
  },
  {
    icon: 'download',
    title: 'Never locked in',
    text: 'Export every post you have written to CSV whenever you like.',
  },
]

/** The welcome block on the home page, for visitors who aren't logged in */
export function Hero() {
  return (
    <section className={styles.hero} aria-labelledby="hero-title">
      <div className={styles.intro}>
        <div>
          <h1 id="hero-title" className={styles.title}>
            Write to think.
            <br />
            <span className={styles.titleMuted}>Publish to connect.</span>
          </h1>
          <p className={styles.lead}>
            The blogging platform for developers and curious minds. Share what you learn, get
            feedback from real readers, and build a body of work that is yours.
          </p>
          <Link to="/register" className={`btn btn-primary ${styles.cta}`}>
            Get started <Icon name="pen" size={18} />
          </Link>
        </div>
        <Illustration />
      </div>

      <ul className={styles.features}>
        {FEATURES.map((feature) => (
          <li key={feature.title} className={styles.feature}>
            <Icon name={feature.icon} size={22} />
            <h2>{feature.title}</h2>
            <p>{feature.text}</p>
          </li>
        ))}
      </ul>
    </section>
  )
}

/** A desk lamp lighting an open book, in single-line strokes */
function Illustration() {
  return (
    <svg className={styles.art} viewBox="0 0 360 260" fill="none" aria-hidden>
      {/* The light falling on the page */}
      <path className={styles.glow} d="M264 104 L120 205 L250 214 L294 126 Z" />

      <g stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        {/* Desk */}
        <path d="M16 232 H344" />

        {/* Open book */}
        <path d="M80 226 Q130 206 180 220 Q230 206 280 226" />
        <path d="M80 226 V160 Q130 140 180 154 V220" />
        <path d="M180 154 Q230 140 280 160 V226" />
        <path d="M98 174 Q128 162 162 170 M98 190 Q128 178 162 186 M98 206 Q120 198 144 202" />
        <path d="M198 170 Q232 162 262 174 M198 186 Q232 178 262 190" />

        {/* Lamp: base, arm, and a cone-shaped shade tilted towards the book */}
        <path d="M300 232 Q300 220 318 220 Q336 220 336 232" />
        <path d="M318 220 L330 150 L311 85" />
        <circle cx="330" cy="150" r="4" />
        <path d="M304 76 L318 94 L294 128 Q272 124 262 102 Z" />
        <path d="M272 114 Q278 124 286 121" />

        {/* A heart floating up from the page */}
        <path d="M150 112 C150 102 136 102 136 112 C136 120 150 128 150 128 C150 128 164 120 164 112 C164 102 150 102 150 112 Z" />
      </g>

      {/* Sparkles, like the logo */}
      <g className={styles.sparkle}>
        <path d="M206 96 L210 108 L222 112 L210 116 L206 128 L202 116 L190 112 L202 108 Z" />
        <path d="M110 128 L112 134 L118 136 L112 138 L110 144 L108 138 L102 136 L108 134 Z" />
      </g>
    </svg>
  )
}
