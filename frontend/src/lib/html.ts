import DOMPurify from 'dompurify'

// The same lists the backend cleans with (backend/app/core/html.py). The server already
// cleans every post; this is a second layer, in case something slips past it.
const TAGS = [
  'p', 'h2', 'h3', 'strong', 'em', 'u', 's', 'a',
  'ul', 'ol', 'li', 'blockquote', 'pre', 'code', 'br', 'hr', 'span',
  'table', 'thead', 'tbody', 'tr', 'th', 'td',
] // prettier-ignore
const STYLED = new Set(['SPAN', 'P', 'H2', 'H3', 'LI'])
const STYLES = new Set(['color', 'font-size', 'font-family', 'text-align'])

// Its own instance, so these hooks don't change DOMPurify for anything else
const purify = DOMPurify(window)

purify.addHook('afterSanitizeAttributes', (node) => {
  if (node instanceof HTMLElement && node.hasAttribute('style')) {
    // Only the four properties the toolbar sets, and only on the tags that take them
    const names = Array.from(node.style)
    for (const name of names) {
      if (!STYLED.has(node.tagName) || !STYLES.has(name)) node.style.removeProperty(name)
    }
    if (node.style.length === 0) node.removeAttribute('style')
  }
  // Links to other sites open in a new tab; noopener stops them controlling this one
  if (node instanceof HTMLAnchorElement && node.href.startsWith('http')) {
    node.target = '_blank'
    node.rel = 'noopener noreferrer'
  }
})

export function cleanHtml(html: string): string {
  return purify.sanitize(html, {
    ALLOWED_TAGS: TAGS,
    ALLOWED_ATTR: ['href', 'style', 'colspan', 'rowspan'],
    ALLOWED_URI_REGEXP: /^(https?:|mailto:)/i,
  })
}
