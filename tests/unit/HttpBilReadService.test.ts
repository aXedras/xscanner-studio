import { describe, expect, test, vi } from 'vitest'
import { HttpBilReadService } from '../../src/services/core/extraction/impl/HttpBilReadService'
import type { HttpJsonClient } from '../../src/services/infrastructure/http/httpClient'
import type { IBilService } from '../../src/services/core/extraction/IBilService'

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
    listRegistrationsByExtractionId: vi.fn(),
    listRegistrationsByExtractionIds: vi.fn(),
    registerOnBil: vi.fn(),
  } satisfies IBilService
}

describe('HttpBilReadService', () => {
  test('fetches single extraction registrations via query endpoint', async () => {
    const client = createClient()
    const fallback = createFallback()
    const logger = createLogger()

    const rows = [{ id: 'bil-1' }]
    client.getJson.mockResolvedValueOnce(rows)

    const service = new HttpBilReadService({ client, fallback, logger })
    const result = await service.listRegistrationsByExtractionId('ext-1')

    expect(client.getJson).toHaveBeenCalledWith('/api/v1/bil/registrations?extraction_id=ext-1')
    expect(result).toEqual(rows)
  })

  test('uses batch endpoint and trims empty ids', async () => {
    const client = createClient()
    const fallback = createFallback()
    const logger = createLogger()

    const rows = [{ id: 'bil-2' }]
    client.postJson.mockResolvedValueOnce(rows)

    const service = new HttpBilReadService({ client, fallback, logger })
    const result = await service.listRegistrationsByExtractionIds([' ext-1 ', '', 'ext-2'])

    expect(client.postJson).toHaveBeenCalledWith('/api/v1/bil/registrations:batch', {
      extraction_ids: ['ext-1', 'ext-2'],
    })
    expect(result).toEqual(rows)
  })
})
