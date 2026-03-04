import { describe, expect, test, vi } from 'vitest'
import { HttpExtractionReadService } from '../../src/services/core/extraction/impl/HttpExtractionReadService'
import { HttpError } from '../../src/services/infrastructure/http/httpClient'
import type { HttpJsonClient } from '../../src/services/infrastructure/http/httpClient'
import type { IExtractionService } from '../../src/services/core/extraction/IExtractionService'

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
    listActive: vi.fn(),
    listActivePaged: vi.fn(),
    getActiveStatusCounts: vi.fn(),
    getActiveByOriginalId: vi.fn(),
    getHistoryByOriginalId: vi.fn(),
    getImagePreviewSrc: vi.fn(),
    extractFromUpload: vi.fn(),
    validateActive: vi.fn(),
    rejectActive: vi.fn(),
    createCorrectionVersion: vi.fn(),
  } satisfies IExtractionService
}

describe('HttpExtractionReadService', () => {
  test('maps paged extraction query to HTTP endpoint', async () => {
    const client = createClient()
    const fallback = createFallback()
    const logger = createLogger()

    client.getJson.mockResolvedValueOnce({
      items: [{ id: 'ext-1' }],
      total: 1,
      page: 1,
      page_size: 10,
    })

    const service = new HttpExtractionReadService({ client, fallback, logger })
    const result = await service.listActivePaged({
      page: 1,
      pageSize: 10,
      statuses: ['pending'],
      search: 'metal',
      sort: { field: 'created_at', direction: 'desc' },
    })

    expect(client.getJson).toHaveBeenCalledWith(
      '/api/v1/extractions?page=1&page_size=10&sort_field=created_at&sort_direction=desc&search=metal&status=pending'
    )
    expect(result.pageSize).toBe(10)
  })

  test('throws when extraction paged response misses page_size', async () => {
    const client = createClient()
    const fallback = createFallback()
    const logger = createLogger()

    client.getJson.mockResolvedValueOnce({
      items: [{ id: 'ext-1' }],
      total: 1,
      page: 1,
    })

    const service = new HttpExtractionReadService({ client, fallback, logger })

    await expect(
      service.listActivePaged({
        page: 1,
        pageSize: 10,
        statuses: ['pending'],
        search: 'metal',
        sort: { field: 'created_at', direction: 'desc' },
      })
    ).rejects.toThrow("expected numeric field 'page_size'")
  })

  test('returns empty list on 404 history lookup', async () => {
    const client = createClient()
    const fallback = createFallback()
    const logger = createLogger()

    client.getJson.mockRejectedValueOnce(
      new HttpError({
        message: 'not found',
        kind: 'http',
        method: 'GET',
        url: '/api/v1/extractions/by-original/missing/history',
        status: 404,
      })
    )

    const service = new HttpExtractionReadService({ client, fallback, logger })
    const result = await service.getHistoryByOriginalId('missing')
    expect(result).toEqual([])
  })

  test('delegates createCorrectionVersion to fallback service', async () => {
    const client = createClient()
    const fallback = createFallback()
    const logger = createLogger()

    const row = { id: 'ext-2' }
    fallback.createCorrectionVersion.mockResolvedValueOnce(row as never)

    const service = new HttpExtractionReadService({ client, fallback, logger })
    const result = await service.createCorrectionVersion({
      originalId: 'orig-1',
      corrected: {
        serial_number: null,
        metal: null,
        weight: null,
        weight_unit: null,
        fineness: null,
        producer: null,
      },
      updatedBy: 'user-1',
    })

    expect(fallback.createCorrectionVersion).toHaveBeenCalled()
    expect(result).toEqual(row)
  })

  test('requests extraction image preview URL via API and maps response URL', async () => {
    const client = createClient()
    const fallback = createFallback()
    const logger = createLogger()

    client.getJson.mockResolvedValueOnce({ signed_url: 'https://cdn.example/extractions/a.jpg?sig=1' })

    const service = new HttpExtractionReadService({ client, fallback, logger })
    const preview = await service.getImagePreviewSrc('extractions/a.jpg')

    expect(client.getJson).toHaveBeenCalledWith('/api/v1/storage/preview?storage_path=extractions%2Fa.jpg')
    expect(preview).toEqual({ src: 'https://cdn.example/extractions/a.jpg?sig=1' })
  })
})
