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
    patchJson: vi.fn(),
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
    client.patchJson.mockResolvedValueOnce(row as never)

    const service = new HttpOrderReadService({ client, fallback, logger })
    const result = await service.updateOrder('order-1', { status: 'validated' })

    expect(client.patchJson).toHaveBeenCalledWith('/api/v1/orders/order-1', { status: 'validated' })
    expect(result).toEqual(row)
  })

  test('requests storage preview URL via API and maps response URL', async () => {
    const client = createClient()
    const fallback = createFallback()
    const logger = createLogger()

    client.getJson.mockResolvedValueOnce({ src: 'https://cdn.example/file.pdf?sig=1', mode: 'signed' })

    const service = new HttpOrderReadService({ client, fallback, logger })
    const preview = await service.getPdfPreviewSrc('orders/a/b.pdf')

    expect(client.getJson).toHaveBeenCalledWith('/api/v1/storage/preview?storage_path=orders%2Fa%2Fb.pdf')
    expect(preview).toEqual({ src: 'https://cdn.example/file.pdf?sig=1' })
  })

  test('resolves original id by searching orders API with order id', async () => {
    const client = createClient()
    const fallback = createFallback()
    const logger = createLogger()

    client.getJson.mockResolvedValueOnce({ original_id: 'orig-456' })

    const service = new HttpOrderReadService({ client, fallback, logger })
    const result = await service.resolveOriginalIdByOrderId('order-123')

    expect(client.getJson).toHaveBeenCalledWith(
      '/api/v1/orders/order-123/resolve-original-id'
    )
    expect(result).toBe('orig-456')
  })

  test('falls back when orders API cannot resolve original id', async () => {
    const client = createClient()
    const fallback = createFallback()
    const logger = createLogger()

    client.getJson.mockResolvedValueOnce({ original_id: null })
    fallback.resolveOriginalIdByOrderId.mockResolvedValueOnce('orig-from-fallback')

    const service = new HttpOrderReadService({ client, fallback, logger })
    const result = await service.resolveOriginalIdByOrderId('order-404')

    expect(result).toBe('orig-from-fallback')
    expect(fallback.resolveOriginalIdByOrderId).toHaveBeenCalledWith('order-404')
  })

  test('calls attribution endpoint with updatedBy payload', async () => {
    const client = createClient()
    const fallback = createFallback()
    const logger = createLogger()

    client.postJson.mockResolvedValueOnce({ ok: true })

    const service = new HttpOrderReadService({ client, fallback, logger })
    await service.attributePersistedSnapshot('order-123', 'user-1')

    expect(client.postJson).toHaveBeenCalledWith('/api/v1/orders/order-123/attribute-persisted-snapshot', {
      updatedBy: 'user-1',
    })
  })
})
