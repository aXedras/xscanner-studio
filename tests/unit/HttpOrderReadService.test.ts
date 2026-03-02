import { describe, expect, test, vi } from 'vitest'
import { HttpOrderReadService } from '../../src/services/core/order/impl/HttpOrderReadService'
import { HttpError } from '../../src/services/infrastructure/http/httpClient'
import type { HttpJsonClient } from '../../src/services/infrastructure/http/httpClient'
import type { IOrderService } from '../../src/services/core/order/IOrderService'

function createLogger() {
  return {
    debug: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
    time: vi.fn(),
    timeEnd: vi.fn(),
    group: vi.fn(),
    groupEnd: vi.fn(),
  }
}

function createClient() {
  return {
    getJson: vi.fn(),
    postJson: vi.fn(),
    postFormData: vi.fn(),
  } satisfies HttpJsonClient
}

function createFallback() {
  return {
    extractFromUpload: vi.fn(),
    extractFromUploadDebug: vi.fn(),
    attributePersistedSnapshot: vi.fn(),
    listActivePaged: vi.fn(),
    getActiveStatusCounts: vi.fn(),
    findActiveByOriginalId: vi.fn(),
    findHistoryByOriginalId: vi.fn(),
    updateOrder: vi.fn(),
    resolveOriginalIdByOrderId: vi.fn(),
    listActiveItems: vi.fn(),
    listActiveItemsByOriginalId: vi.fn(),
    findItemHistoryByOriginalId: vi.fn(),
    createItem: vi.fn(),
    updateItem: vi.fn(),
    deleteItem: vi.fn(),
    getPdfPreviewSrc: vi.fn(),
  } satisfies IOrderService
}

describe('HttpOrderReadService', () => {
  test('maps list query to HTTP endpoint and normalizes pageSize from snake_case', async () => {
    const client = createClient()
    const fallback = createFallback()
    const logger = createLogger()

    client.getJson.mockResolvedValueOnce({
      items: [{ id: '1' }],
      total: 1,
      page: 2,
      page_size: 25,
    })

    const service = new HttpOrderReadService({ client, fallback, logger })
    const result = await service.listActivePaged({
      page: 2,
      pageSize: 25,
      search: 'abc',
      statuses: ['pending'],
      sort: { field: 'created_at', direction: 'desc' },
    })

    expect(client.getJson).toHaveBeenCalledWith(
      '/api/v1/orders?page=2&page_size=25&sort_field=created_at&sort_direction=desc&search=abc&status=pending'
    )
    expect(result.pageSize).toBe(25)
    expect(result.total).toBe(1)
  })

  test('throws when paged response misses page_size', async () => {
    const client = createClient()
    const fallback = createFallback()
    const logger = createLogger()

    client.getJson.mockResolvedValueOnce({
      items: [{ id: '1' }],
      total: 1,
      page: 2,
    })

    const service = new HttpOrderReadService({ client, fallback, logger })

    await expect(
      service.listActivePaged({
        page: 2,
        pageSize: 25,
        search: 'abc',
        statuses: ['pending'],
        sort: { field: 'created_at', direction: 'desc' },
      })
    ).rejects.toThrow("expected numeric field 'page_size'")
  })

  test('returns null on 404 for active-by-original lookup', async () => {
    const client = createClient()
    const fallback = createFallback()
    const logger = createLogger()

    client.getJson.mockRejectedValueOnce(
      new HttpError({
        message: 'not found',
        kind: 'http',
        method: 'GET',
        url: '/api/v1/orders/by-original/missing/active',
        status: 404,
      })
    )

    const service = new HttpOrderReadService({ client, fallback, logger })
    const result = await service.findActiveByOriginalId('missing')

    expect(result).toBeNull()
  })

  test('delegates write operations to fallback service', async () => {
    const client = createClient()
    const fallback = createFallback()
    const logger = createLogger()

    const row = { id: 'order-1' }
    fallback.updateOrder.mockResolvedValueOnce(row as never)

    const service = new HttpOrderReadService({ client, fallback, logger })
    const result = await service.updateOrder('order-1', { status: 'validated' })

    expect(fallback.updateOrder).toHaveBeenCalledWith('order-1', { status: 'validated' })
    expect(result).toEqual(row)
  })
})
