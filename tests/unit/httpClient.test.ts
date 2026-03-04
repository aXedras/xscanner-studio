import { describe, expect, test, vi } from 'vitest'

import type { ILogger } from '@/lib/utils/logging'
import { createHttpJsonClient, HttpError, joinUrl } from '@/services/infrastructure/http/httpClient'

function createNoopLogger(): ILogger {
  return {
    debug: () => {},
    info: () => {},
    warn: () => {},
    error: () => {},
    time: () => {},
    timeEnd: () => {},
    group: () => {},
    groupEnd: () => {},
  }
}

function createJsonResponse(payload: unknown, init?: { ok?: boolean; status?: number }): Response {
  const ok = init?.ok ?? true
  const status = init?.status ?? 200

  return {
    ok,
    status,
    text: async () => JSON.stringify(payload),
  } as unknown as Response
}

function createTextResponse(text: string, init?: { ok?: boolean; status?: number }): Response {
  const ok = init?.ok ?? true
  const status = init?.status ?? 200

  return {
    ok,
    status,
    text: async () => text,
  } as unknown as Response
}

describe('httpClient (unit, black-box)', () => {
  test('joinUrl joins without double slashes', () => {
    expect(joinUrl('http://x.test/', '/a/', 'b')).toBe('http://x.test/a/b')
    expect(joinUrl('http://x.test///', '///a///')).toBe('http://x.test/a')
    expect(joinUrl('http://x.test/', '', undefined, null)).toBe('http://x.test')
  })

  test('getJson parses JSON response', async () => {
    const fetchMock = vi.fn().mockResolvedValue(createJsonResponse({ hello: 'world' }))
    vi.stubGlobal('fetch', fetchMock)

    const client = createHttpJsonClient({ baseUrl: 'http://x.test/', logger: createNoopLogger() })
    const result = await client.getJson<{ hello: string }>('/hello')

    expect(result).toEqual({ hello: 'world' })
    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('http://x.test/hello')
    expect(init.method).toBe('GET')
    expect(init.credentials).toBe('same-origin')
  })

  test('postJson sends JSON body and content-type header', async () => {
    const fetchMock = vi.fn().mockResolvedValue(createJsonResponse({ ok: true }))
    vi.stubGlobal('fetch', fetchMock)

    const client = createHttpJsonClient({ baseUrl: 'http://x.test', logger: createNoopLogger() })
    await client.postJson('/submit', { a: 1 })

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('http://x.test/submit')
    expect(init.method).toBe('POST')
    expect(init.body).toBe(JSON.stringify({ a: 1 }))
    expect((init.headers as Record<string, string>)['Content-Type']).toBe('application/json')
  })

  test('throws HttpError(kind=http) on non-2xx response', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(createJsonResponse({ detail: 'bad request' }, { ok: false, status: 400 }))
    vi.stubGlobal('fetch', fetchMock)

    const client = createHttpJsonClient({ baseUrl: 'http://x.test', logger: createNoopLogger() })

    const promise = client.getJson('/oops')
    await expect(promise).rejects.toBeInstanceOf(HttpError)
    await expect(promise).rejects.toMatchObject({
      kind: 'http',
      method: 'GET',
      status: 400,
      url: 'http://x.test/oops',
    })
  })

  test('throws HttpError(kind=invalid_json) when response is not JSON', async () => {
    const fetchMock = vi.fn().mockResolvedValue(createTextResponse('not json', { ok: true, status: 200 }))
    vi.stubGlobal('fetch', fetchMock)

    const client = createHttpJsonClient({ baseUrl: 'http://x.test', logger: createNoopLogger() })

    const promise = client.getJson('/invalid')
    await expect(promise).rejects.toBeInstanceOf(HttpError)
    await expect(promise).rejects.toMatchObject({
      kind: 'invalid_json',
      method: 'GET',
      status: 200,
      url: 'http://x.test/invalid',
    })
  })

  test('throws HttpError(kind=network) on fetch failure', async () => {
    const fetchMock = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'))
    vi.stubGlobal('fetch', fetchMock)

    const client = createHttpJsonClient({ baseUrl: 'http://x.test', logger: createNoopLogger() })

    const promise = client.getJson('/down')
    await expect(promise).rejects.toBeInstanceOf(HttpError)
    await expect(promise).rejects.toMatchObject({
      kind: 'network',
      method: 'GET',
      url: 'http://x.test/down',
    })
  })

  test('throws HttpError(kind=aborted) when fetch aborts (no timeout)', async () => {
    const fetchMock = vi.fn().mockRejectedValue(new DOMException('Aborted', 'AbortError'))
    vi.stubGlobal('fetch', fetchMock)

    const client = createHttpJsonClient({ baseUrl: 'http://x.test', logger: createNoopLogger(), timeoutMs: 30_000 })

    const promise = client.getJson('/aborted')
    await expect(promise).rejects.toBeInstanceOf(HttpError)
    await expect(promise).rejects.toMatchObject({
      kind: 'aborted',
      method: 'GET',
      url: 'http://x.test/aborted',
    })
  })

  test('throws HttpError(kind=timeout) when fetch does not resolve in time', async () => {
    vi.useFakeTimers()

    const fetchMock = vi.fn().mockImplementation((_url: string, init?: RequestInit) => {
      return new Promise((_resolve, reject) => {
        const signal = init?.signal as AbortSignal | undefined
        if (!signal) return

        if (signal.aborted) {
          reject(new DOMException('Aborted', 'AbortError'))
          return
        }

        signal.addEventListener(
          'abort',
          () => {
            reject(new DOMException('Aborted', 'AbortError'))
          },
          { once: true }
        )
      })
    })

    vi.stubGlobal('fetch', fetchMock)

    const client = createHttpJsonClient({ baseUrl: 'http://x.test', logger: createNoopLogger(), timeoutMs: 5 })
    const promise = client.getJson('/slow')
    const handled = promise.then(
      () => ({ ok: true as const }),
      (error: unknown) => ({ ok: false as const, error })
    )

    await vi.advanceTimersByTimeAsync(10)

    const outcome = await handled
    expect(outcome.ok).toBe(false)

    if (outcome.ok) {
      throw new Error('Expected request to time out')
    }

    expect(outcome.error).toBeInstanceOf(HttpError)
    expect(outcome.error).toMatchObject({
      kind: 'timeout',
      method: 'GET',
      url: 'http://x.test/slow',
    })

    vi.useRealTimers()
  })

  test('requestOptions.timeoutMs overrides client timeout for a single request', async () => {
    vi.useFakeTimers()

    const fetchMock = vi.fn().mockImplementation((_url: string, init?: RequestInit) => {
      return new Promise((_resolve, reject) => {
        const signal = init?.signal as AbortSignal | undefined
        if (!signal) return

        if (signal.aborted) {
          reject(new DOMException('Aborted', 'AbortError'))
          return
        }

        signal.addEventListener(
          'abort',
          () => {
            reject(new DOMException('Aborted', 'AbortError'))
          },
          { once: true }
        )
      })
    })

    vi.stubGlobal('fetch', fetchMock)

    const client = createHttpJsonClient({ baseUrl: 'http://x.test', logger: createNoopLogger(), timeoutMs: 50 })
    const promise = client.getJson('/slow', { timeoutMs: 5 })
    const handled = promise.then(
      () => ({ ok: true as const }),
      (error: unknown) => ({ ok: false as const, error })
    )

    await vi.advanceTimersByTimeAsync(10)

    const outcome = await handled
    expect(outcome.ok).toBe(false)

    if (outcome.ok) {
      throw new Error('Expected request to time out')
    }

    expect(outcome.error).toBeInstanceOf(HttpError)
    expect(outcome.error).toMatchObject({
      kind: 'timeout',
      method: 'GET',
      url: 'http://x.test/slow',
    })

    vi.useRealTimers()
  })
})
