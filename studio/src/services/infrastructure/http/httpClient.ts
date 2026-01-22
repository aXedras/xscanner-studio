import type { ILogger } from '../../../lib/utils/logging'

export type HttpErrorKind = 'http' | 'network' | 'timeout' | 'aborted' | 'invalid_json'

export class HttpError extends Error {
  readonly kind: HttpErrorKind
  readonly method: string
  readonly url: string
  readonly status?: number
  readonly payloadSnippet?: string
  readonly responseSnippet?: string
  readonly cause?: unknown

  constructor(input: {
    message: string
    kind: HttpErrorKind
    method: string
    url: string
    status?: number
    payloadSnippet?: string
    responseSnippet?: string
    cause?: unknown
  }) {
    super(input.message)
    this.name = 'HttpError'
    this.kind = input.kind
    this.method = input.method
    this.url = input.url
    this.status = input.status
    this.payloadSnippet = input.payloadSnippet
    this.responseSnippet = input.responseSnippet
    this.cause = input.cause
  }
}

export function joinUrl(baseUrl: string, ...parts: Array<string | null | undefined>): string {
  const base = baseUrl.replace(/\/+$/, '')
  const cleaned = parts
    .filter((part): part is string => Boolean(part && part.trim()))
    .map(part => part.replace(/^\/+/, '').replace(/\/+$/, ''))
    .filter(Boolean)

  if (cleaned.length === 0) return base
  return `${base}/${cleaned.join('/')}`
}

type HttpClientOptions = {
  baseUrl: string
  logger: ILogger
  name?: string
  defaultHeaders?: Record<string, string>
  timeoutMs?: number
  maxSnippetChars?: number
}

type RequestOptions = {
  headers?: Record<string, string>
  timeoutMs?: number
}

export type HttpJsonClient = {
  getJson<TResponse>(path: string, options?: RequestOptions): Promise<TResponse>
  postJson<TResponse>(path: string, body: unknown, options?: RequestOptions): Promise<TResponse>
  postFormData<TResponse>(path: string, formData: FormData, options?: RequestOptions): Promise<TResponse>
}

function truncate(text: string, maxChars: number): string {
  if (text.length <= maxChars) return text
  return `${text.slice(0, maxChars)}…`
}

function safeJsonSnippet(value: unknown, maxChars: number): string {
  try {
    return truncate(JSON.stringify(value), maxChars)
  } catch {
    return '[unserializable json]'
  }
}

function describeFormData(formData: FormData): string {
  const keys = new Set<string>()
  for (const [key] of formData.entries()) {
    keys.add(key)
  }
  return `FormData(keys=${Array.from(keys).sort().join(',')})`
}

class FetchTimeoutError extends Error {
  readonly cause?: unknown

  constructor(cause?: unknown) {
    super('Request timed out')
    this.name = 'FetchTimeoutError'
    this.cause = cause
  }
}

function classifyFetchError(error: unknown): HttpErrorKind {
  if (error instanceof FetchTimeoutError) return 'timeout'
  if (error instanceof DOMException && error.name === 'AbortError') return 'aborted'
  return 'network'
}

async function fetchWithTimeout(input: { url: string; init: RequestInit; timeoutMs: number }): Promise<Response> {
  const controller = new AbortController()
  const timeoutApi = globalThis.setTimeout
  const clearTimeoutApi = globalThis.clearTimeout
  let didTimeout = false

  const timeoutId = timeoutApi(() => {
    didTimeout = true
    controller.abort()
  }, input.timeoutMs)

  try {
    try {
      return await fetch(input.url, {
        ...input.init,
        signal: controller.signal,
      })
    } catch (error) {
      if (didTimeout) {
        throw new FetchTimeoutError(error)
      }
      throw error
    }
  } finally {
    clearTimeoutApi(timeoutId)
  }
}

export function createHttpJsonClient(options: HttpClientOptions): HttpJsonClient {
  const {
    baseUrl,
    logger,
    name = 'HttpJsonClient',
    defaultHeaders = {},
    timeoutMs = 30_000,
    maxSnippetChars = 2_000,
  } = options

  const request = async <TResponse>(input: {
    method: string
    path: string
    headers?: Record<string, string>
    body?: BodyInit | null
    payloadSnippet?: string
    timeoutMs?: number
  }): Promise<TResponse> => {
    const url = joinUrl(baseUrl, input.path)
    const startedAt = performance.now()

    const effectiveTimeoutMs = input.timeoutMs ?? timeoutMs

    logger.debug(name, 'http.request', { method: input.method, url })

    let response: Response
    try {
      response = await fetchWithTimeout({
        url,
        timeoutMs: effectiveTimeoutMs,
        init: {
          method: input.method,
          headers: { ...defaultHeaders, ...(input.headers ?? {}) },
          body: input.body,
        },
      })
    } catch (error) {
      const kind = classifyFetchError(error)
      const err = new HttpError({
        message: `Request failed (${kind})`,
        kind,
        method: input.method,
        url,
        payloadSnippet: input.payloadSnippet,
        cause: error,
      })

      logger.error(name, 'http.request_failed', err)
      throw err
    }

    const durationMs = Math.round(performance.now() - startedAt)
    const text = await response.text()
    const responseSnippet = text ? truncate(text, maxSnippetChars) : undefined

    let payload: unknown = null
    if (text) {
      try {
        payload = JSON.parse(text) as unknown
      } catch (error) {
        const err = new HttpError({
          message: `Invalid JSON response (status=${response.status})`,
          kind: 'invalid_json',
          method: input.method,
          url,
          status: response.status,
          payloadSnippet: input.payloadSnippet,
          responseSnippet,
          cause: error,
        })

        logger.error(name, 'http.invalid_json', err)
        throw err
      }
    }

    if (!response.ok) {
      const err = new HttpError({
        message: `HTTP ${response.status} for ${input.method} ${url}`,
        kind: 'http',
        method: input.method,
        url,
        status: response.status,
        payloadSnippet: input.payloadSnippet,
        responseSnippet: payload ? safeJsonSnippet(payload, maxSnippetChars) : responseSnippet,
      })

      if (response.status >= 400 && response.status < 500) {
        logger.warn(name, 'http.response_4xx', { status: response.status, url, durationMs, error: err })
      } else {
        logger.error(name, 'http.response_5xx', err)
      }

      throw err
    }

    logger.debug(name, 'http.response', { method: input.method, url, status: response.status, durationMs })
    return payload as TResponse
  }

  return {
    async getJson<TResponse>(path: string, requestOptions?: RequestOptions): Promise<TResponse> {
      return await request<TResponse>({
        method: 'GET',
        path,
        headers: { ...(requestOptions?.headers ?? {}) },
        timeoutMs: requestOptions?.timeoutMs,
      })
    },

    async postJson<TResponse>(path: string, body: unknown, requestOptions?: RequestOptions): Promise<TResponse> {
      const payloadSnippet = safeJsonSnippet(body, maxSnippetChars)
      return await request<TResponse>({
        method: 'POST',
        path,
        headers: {
          'Content-Type': 'application/json',
          ...(requestOptions?.headers ?? {}),
        },
        body: JSON.stringify(body),
        payloadSnippet,
        timeoutMs: requestOptions?.timeoutMs,
      })
    },

    async postFormData<TResponse>(
      path: string,
      formData: FormData,
      requestOptions?: RequestOptions
    ): Promise<TResponse> {
      return await request<TResponse>({
        method: 'POST',
        path,
        headers: { ...(requestOptions?.headers ?? {}) },
        body: formData,
        payloadSnippet: truncate(describeFormData(formData), maxSnippetChars),
        timeoutMs: requestOptions?.timeoutMs,
      })
    },
  }
}
