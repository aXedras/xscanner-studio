import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'

import { ServiceFactory } from '../../src/services/factory/ServiceFactory'
import type { ILogger } from '../../src/lib/utils/logging'

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

function resetServiceFactorySingleton(): void {
  ;(ServiceFactory as unknown as { instance: unknown }).instance = null
}

type FetchRequestInput = Parameters<typeof fetch>[0]

function isFetchRequestInput(input: unknown): input is FetchRequestInput {
  return typeof input === 'string' || input instanceof URL || input instanceof Request
}

function getRequestUrl(input: FetchRequestInput): string {
  if (typeof input === 'string') return input
  if (input instanceof URL) return input.toString()
  return input.url
}

describe('Auth API adapter (integration with mocked API)', () => {
  const logger = createNoopLogger()

  beforeEach(() => {
    resetServiceFactorySingleton()
    globalThis.window.__ENV__ = {
      VITE_USE_AUTH_API: 'true',
      VITE_API_URL: 'http://localhost:8000',
    }
  })

  afterEach(() => {
    vi.restoreAllMocks()
    resetServiceFactorySingleton()
    globalThis.window.__ENV__ = {}
  })

  test('routes sign-in via /api/v1/auth/sign-in when auth API flag is enabled', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(async input => {
      const url = getRequestUrl(input)
      if (url === 'http://localhost:8000/api/v1/auth/sign-in') {
        return new Response(JSON.stringify({ hasSession: true }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
      }

      return new Response(JSON.stringify({ error: 'unexpected path' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      })
    })

    const services = ServiceFactory.getInstance({
      logger,
    })

    const result = await services.authService.signIn({
      email: 'user@example.com',
      password: 'secret',
    })

    expect(result).toEqual({ hasSession: true })
    expect(fetchMock).toHaveBeenCalledTimes(1)
    const firstCallInput = fetchMock.mock.calls[0]?.[0]
    expect(isFetchRequestInput(firstCallInput)).toBe(true)
    if (!isFetchRequestInput(firstCallInput)) {
      throw new Error('Expected first fetch argument to be a URL-like input.')
    }
    expect(getRequestUrl(firstCallInput)).toBe('http://localhost:8000/api/v1/auth/sign-in')
  })

  test('routes session lookup via /api/v1/auth/session when auth API flag is enabled', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(async input => {
      const url = getRequestUrl(input)
      if (url === 'http://localhost:8000/api/v1/auth/session') {
        return new Response(
          JSON.stringify({
            session: {
              id: 'user-1',
              email: 'user@example.com',
              user_metadata: { display_name: 'User One' },
            },
          }),
          {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          }
        )
      }

      return new Response(JSON.stringify({ error: 'unexpected path' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      })
    })

    const services = ServiceFactory.getInstance({
      logger,
    })

    const result = await services.authService.getSession()

    expect(result).toEqual({
      session: {
        id: 'user-1',
        email: 'user@example.com',
        user_metadata: { display_name: 'User One' },
      },
    })
    expect(fetchMock).toHaveBeenCalledTimes(1)
    const firstCallInput = fetchMock.mock.calls[0]?.[0]
    expect(isFetchRequestInput(firstCallInput)).toBe(true)
    if (!isFetchRequestInput(firstCallInput)) {
      throw new Error('Expected first fetch argument to be a URL-like input.')
    }
    expect(getRequestUrl(firstCallInput)).toBe('http://localhost:8000/api/v1/auth/session')
  })
})
