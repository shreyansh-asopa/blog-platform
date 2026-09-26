/**
 * The one place that talks to the API. It adds the login token, turns the backend's
 * {"error": {code, message, ...}} bodies into an ApiError, and parses JSON.
 */

const BASE = '/api/v1'
const TOKEN_KEY = 'lumen-token'

export interface FieldError {
  field: string
  message: string
}

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly requestId?: string
  readonly details: FieldError[]

  constructor(
    status: number,
    code: string,
    message: string,
    requestId?: string,
    details: FieldError[] = [],
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.requestId = requestId
    this.details = details
  }
}

// localStorage can throw (private mode, blocked storage), so every access is guarded
export const tokenStore = {
  get(): string | null {
    try {
      return localStorage.getItem(TOKEN_KEY)
    } catch {
      return null
    }
  },
  set(token: string | null) {
    try {
      if (token) localStorage.setItem(TOKEN_KEY, token)
      else localStorage.removeItem(TOKEN_KEY)
    } catch {
      // The token then lasts only until the page is reloaded
    }
  },
}

// Set by the auth provider, so a rejected token logs the user out everywhere at once
let onUnauthorized: () => void = () => {}
export function setUnauthorizedHandler(handler: () => void) {
  onUnauthorized = handler
}

type Body = FormData | URLSearchParams | object

export async function api<T>(
  path: string,
  options: { method?: string; body?: Body } = {},
): Promise<T> {
  const headers = new Headers()
  const token = tokenStore.get()
  if (token) headers.set('Authorization', `Bearer ${token}`)

  let body: BodyInit | undefined
  if (options.body instanceof FormData || options.body instanceof URLSearchParams) {
    body = options.body // the browser sets the matching Content-Type itself
  } else if (options.body !== undefined) {
    body = JSON.stringify(options.body)
    headers.set('Content-Type', 'application/json')
  }

  let response: Response
  try {
    response = await fetch(BASE + path, { method: options.method ?? 'GET', headers, body })
  } catch {
    throw new ApiError(0, 'network_error', 'Could not reach the server. Is the API running?')
  }

  if (response.status === 401 && token) onUnauthorized()
  if (!response.ok) throw await toApiError(response)
  if (response.status === 204) return undefined as T
  try {
    return (await response.json()) as T
  } catch {
    // e.g. the dev proxy is off and Vite answered with index.html
    throw new ApiError(response.status, 'invalid_response', 'The server sent an unexpected reply.')
  }
}

/**
 * Downloads a file that needs the login token, so a plain <a href> won't do: fetch it,
 * then hand the browser a temporary blob: URL to save.
 */
export async function download(path: string, fallbackName: string): Promise<void> {
  const headers = new Headers()
  const token = tokenStore.get()
  if (token) headers.set('Authorization', `Bearer ${token}`)

  let response: Response
  try {
    response = await fetch(BASE + path, { headers })
  } catch {
    throw new ApiError(0, 'network_error', 'Could not reach the server. Is the API running?')
  }
  if (response.status === 401 && token) onUnauthorized()
  if (!response.ok) throw await toApiError(response)

  // The server names the file in Content-Disposition: attachment; filename="..."
  const disposition = response.headers.get('Content-Disposition') ?? ''
  const filename = /filename="([^"]+)"/.exec(disposition)?.[1] ?? fallbackName

  const url = URL.createObjectURL(await response.blob())
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

async function toApiError(response: Response): Promise<ApiError> {
  try {
    const { error } = await response.json()
    return new ApiError(response.status, error.code, error.message, error.request_id, error.details)
  } catch {
    // Not our JSON shape, e.g. a proxy error page
    return new ApiError(response.status, 'unknown_error', `Request failed (${response.status})`)
  }
}
