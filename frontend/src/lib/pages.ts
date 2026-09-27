/**
 * The page numbers to show: always the first and last, plus the pages next to the current
 * one, with null where a gap is skipped. On page 5 of 12: 1 … 4 5 6 … 12
 */
export function pageNumbers(page: number, pages: number): (number | null)[] {
  const wanted = [...new Set([1, page - 1, page, page + 1, pages])]
    .filter((n) => n >= 1 && n <= pages)
    .sort((a, b) => a - b)
  const out: (number | null)[] = []
  for (const n of wanted) {
    const last = out.at(-1)
    // A gap of exactly one page shows that page, since "…" would take the same room
    if (typeof last === 'number' && n - last === 2) out.push(last + 1)
    else if (typeof last === 'number' && n - last > 2) out.push(null)
    out.push(n)
  }
  return out
}
