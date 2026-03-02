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

describe('Service read adapters (integration with mocked API)', () => {
  const logger = createNoopLogger()

  beforeEach(() => {
    resetServiceFactorySingleton()

    globalThis.window.__ENV__ = {
      VITE_USE_ORDERS_READ_API: 'true',
      VITE_USE_EXTRACTIONS_READ_API: 'true',
      VITE_USE_BIL_READ_API: 'true',
      VITE_USE_EXTRACTIONS_MUTATION_API: 'false',
      VITE_API_URL: 'http://localhost:8000',
    }
  })

  afterEach(() => {
    vi.restoreAllMocks()
    resetServiceFactorySingleton()
    globalThis.window.__ENV__ = {}
  })

  test('routes order read flow through HTTP adapter when read flag is enabled', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(async input => {
      const url = getRequestUrl(input)

      if (url.startsWith('http://localhost:8000/api/v1/orders?')) {
        return new Response(
          JSON.stringify({
            items: [{ id: 'order-1' }],
            total: 1,
            page: 1,
            page_size: 10,
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        )
      }

      return new Response(JSON.stringify({ error: 'unexpected path' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      })
    })

    const services = ServiceFactory.getInstance({
      supabase: {} as never,
      logger,
    })

    const result = await services.orderService.listActivePaged({
      page: 1,
      pageSize: 10,
      statuses: ['pending'],
      search: 'abc',
      sort: { field: 'created_at', direction: 'desc' },
    })

    expect(result.items).toEqual([{ id: 'order-1' }])
    expect(result.total).toBe(1)
    expect(fetchMock).toHaveBeenCalledTimes(1)

    const firstCallInput = fetchMock.mock.calls[0]?.[0]
    expect(isFetchRequestInput(firstCallInput)).toBe(true)
    if (!isFetchRequestInput(firstCallInput)) {
      throw new Error('Expected first fetch argument to be a URL-like input.')
    }
    const requestedUrl = getRequestUrl(firstCallInput)
    expect(requestedUrl).toContain('/api/v1/orders?')
    expect(requestedUrl).toContain('search=abc')
    expect(requestedUrl).toContain('status=pending')
  })

  test('routes extraction and bil read flows through HTTP adapters when read flags are enabled', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(async input => {
      const url = getRequestUrl(input)

      if (url.startsWith('http://localhost:8000/api/v1/extractions?')) {
        return new Response(
          JSON.stringify({
            items: [{ id: 'ext-1' }],
            total: 1,
            page: 1,
            page_size: 20,
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        )
      }

      if (url === 'http://localhost:8000/api/v1/bil/registrations?extraction_id=ext-1') {
        return new Response(JSON.stringify([{ id: 'bil-1', extraction_id: 'ext-1' }]), {
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
      supabase: {} as never,
      logger,
    })

    const extractionResult = await services.extractionService.listActivePaged({
      page: 1,
      pageSize: 20,
      statuses: ['pending'],
      search: 'metal',
      sort: { field: 'created_at', direction: 'desc' },
    })

    const bilResult = await services.bilService.listRegistrationsByExtractionId('ext-1')

    expect(extractionResult.items).toEqual([{ id: 'ext-1' }])
    expect(extractionResult.pageSize).toBe(20)
    expect(bilResult).toEqual([{ id: 'bil-1', extraction_id: 'ext-1' }])
    expect(fetchMock).toHaveBeenCalledTimes(2)

    const requestedUrls = fetchMock.mock.calls
      .map(call => call[0])
      .filter(isFetchRequestInput)
      .map(getRequestUrl)
    expect(requestedUrls.some(url => url.includes('/api/v1/extractions?'))).toBe(true)
    expect(requestedUrls).toContain('http://localhost:8000/api/v1/bil/registrations?extraction_id=ext-1')
  })
})
