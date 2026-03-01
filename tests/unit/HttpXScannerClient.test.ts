import { describe, expect, test, vi } from 'vitest'

import type { ILogger } from '@/lib/utils/logging'
import { HttpXScannerClient } from '@/services/infrastructure/xscanner/HttpXScannerClient'

function createTestLogger(): ILogger {
  const noop = vi.fn()
  return {
    debug: noop,
    info: noop,
    warn: noop,
    error: noop,
    time: noop,
    timeEnd: noop,
    group: noop,
    groupEnd: noop,
  }
}

function createTestImageFile(): File {
  // Unit tests must not rely on repo-bundled binary fixtures.
  // Use an in-memory payload to keep CI deterministic.
  const bytes = new Uint8Array([0xff, 0xd8, 0xff, 0xdb, 0x00, 0x43, 0x00, 0xff, 0xd9])
  return new File([bytes], 'Gold_00250g_9999_E16473_Degussa.jpg', { type: 'image/jpeg' })
}

function createTestPdfFile(): File {
  const bytes = new Uint8Array([0x25, 0x50, 0x44, 0x46, 0x2d, 0x31, 0x2e, 0x34]) // %PDF-1.4
  return new File([bytes], 'order.pdf', { type: 'application/pdf' })
}

describe('HttpXScannerClient (unit)', () => {
  test('extractFromUpload sends correct FormData and returns payload', async () => {
    const logger = createTestLogger()
    const client = new HttpXScannerClient(logger, 'http://xscanner.test/')

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      text: async () =>
        JSON.stringify({
          success: true,
          request_id: 'req_test_123',
          structured_data: { SerialNumber: 'TEST-001' },
          extraction_id: 'ext_1',
          confidence: 0.99,
          processing_time: 0.1,
          strategy_used: 'mock',
          error: null,
          registration: null,
        }),
    })

    vi.stubGlobal('fetch', fetchMock)

    const file = createTestImageFile()

    const result = await client.extractFromUpload({
      file,
      strategy: 'cloud',
      useMock: true,
      registerOnBil: false,
    })

    expect(fetchMock).toHaveBeenCalledTimes(1)

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('http://xscanner.test/extract/upload')
    expect(init.method).toBe('POST')
    expect(init.body).toBeInstanceOf(FormData)

    const form = init.body as FormData
    const entries = Array.from(form.entries())
    const valuesByKey = new Map<string, Array<string | File>>()
    for (const [key, value] of entries) {
      const list = valuesByKey.get(key) ?? []
      list.push(value as string | File)
      valuesByKey.set(key, list)
    }

    expect(valuesByKey.get('strategy')?.[0]).toBe('cloud')
    expect(valuesByKey.get('use_mock')?.[0]).toBe('true')
    expect(valuesByKey.get('register_on_bil')?.[0]).toBe('false')

    const fileValue = valuesByKey.get('file')?.[0]
    expect(fileValue).toBeInstanceOf(File)
    expect((fileValue as File).name).toBe('Gold_00250g_9999_E16473_Degussa.jpg')

    expect(result.success).toBe(true)
    expect(result.request_id).toBe('req_test_123')
  })

  test('extractOrderFromUpload sends pdf as multipart file', async () => {
    const logger = createTestLogger()
    const client = new HttpXScannerClient(logger, 'http://xscanner.test/')

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      text: async () =>
        JSON.stringify({
          success: true,
          request_id: 'req_order_1',
          order_id: 'order_1',
          result: { structured_data: {}, meta: {}, raw: null },
          processing_time: 0.1,
          strategy_used: 'manual',
          error: null,
        }),
    })

    vi.stubGlobal('fetch', fetchMock)

    const file = createTestPdfFile()

    await client.extractOrderFromUpload({
      files: [file],
      strategy: 'manual',
      useMock: true,
    })

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]

    expect(url).toContain('http://xscanner.test/order/extract/upload')
    expect(init.method).toBe('POST')
    expect(init.body).toBeInstanceOf(FormData)
    expect((init.headers as Record<string, string> | undefined)?.['X-Actor-Id']).toBeUndefined()

    const form = init.body as FormData
    const entries = Array.from(form.entries())
    const valuesByKey = new Map<string, Array<string | File>>()
    for (const [key, value] of entries) {
      const list = valuesByKey.get(key) ?? []
      list.push(value as string | File)
      valuesByKey.set(key, list)
    }

    const fileValue = valuesByKey.get('file')?.[0]
    expect(fileValue).toBeInstanceOf(File)
    expect((fileValue as File).name).toBe('order.pdf')
  })
})
