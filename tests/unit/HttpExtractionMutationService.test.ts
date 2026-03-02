import { describe, expect, test, vi } from 'vitest'
import { HttpExtractionMutationService } from '../../src/services/core/extraction/impl/HttpExtractionMutationService'
import type { HttpJsonClient } from '../../src/services/infrastructure/http/httpClient'

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
    listActive: vi.fn(),
    listActivePaged: vi.fn(),
    getActiveStatusCounts: vi.fn(),
    getActiveByOriginalId: vi.fn(),
    getHistoryByOriginalId: vi.fn(),
    extractFromUpload: vi.fn(),
    validateActive: vi.fn(),
    rejectActive: vi.fn(),
    createCorrectionVersion: vi.fn(),
  }
}

describe('HttpExtractionMutationService', () => {
  test('calls validate endpoint with updatedBy payload', async () => {
    const client = createClient()
    const fallback = createFallback()
    const logger = createLogger()

    const row = { id: 'ext-1', status: 'validated' }
    client.postJson.mockResolvedValueOnce(row)

    const service = new HttpExtractionMutationService({ client, fallback, logger })
    const result = await service.validateActive({ originalId: 'orig-1', updatedBy: 'user-1' })

    expect(client.postJson).toHaveBeenCalledWith('/api/v1/extractions/orig-1/validate', { updatedBy: 'user-1' })
    expect(result).toEqual(row)
  })

  test('calls reject endpoint with updatedBy payload', async () => {
    const client = createClient()
    const fallback = createFallback()
    const logger = createLogger()

    const row = { id: 'ext-1', status: 'rejected' }
    client.postJson.mockResolvedValueOnce(row)

    const service = new HttpExtractionMutationService({ client, fallback, logger })
    const result = await service.rejectActive({ originalId: 'orig-2', updatedBy: 'user-2' })

    expect(client.postJson).toHaveBeenCalledWith('/api/v1/extractions/orig-2/reject', { updatedBy: 'user-2' })
    expect(result).toEqual(row)
  })

  test('delegates read methods to fallback service', async () => {
    const client = createClient()
    const fallback = createFallback()
    const logger = createLogger()

    const rows = [{ id: 'a' }]
    fallback.listActive.mockResolvedValueOnce(rows)

    const service = new HttpExtractionMutationService({ client, fallback, logger })
    const result = await service.listActive()

    expect(fallback.listActive).toHaveBeenCalled()
    expect(result).toEqual(rows)
  })
})
