// The search page's URL: /search?q=…&topic=…&topic=…

/** Builds the search URL's query, leaving out what's empty (and page 1) */
export function searchParams(q: string, topics: string[], page = 1) {
  const params = new URLSearchParams()
  if (q) params.set('q', q)
  for (const topic of topics) params.append('topic', topic)
  if (page > 1) params.set('page', String(page))
  return params
}

/** The topics in a URL: lower case, each once */
export const topicsIn = (params: URLSearchParams) => [
  ...new Set(
    params
      .getAll('topic')
      .map((t) => t.trim().toLowerCase())
      .filter(Boolean),
  ),
]
