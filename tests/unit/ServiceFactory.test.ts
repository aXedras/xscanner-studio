import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'

import type { ILogger } from '../../src/lib/utils/logging'
import { ServiceFactory } from '../../src/services/factory/ServiceFactory'

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

describe('ServiceFactory API adapter configuration', () => {
  beforeEach(() => {
    resetServiceFactorySingleton()
    globalThis.window.__ENV__ = {}
    vi.unstubAllEnvs()
  })

  afterEach(() => {
    resetServiceFactorySingleton()
    globalThis.window.__ENV__ = {}
    vi.unstubAllEnvs()
  })

  test('uses default API base URL when VITE_API_URL is missing', () => {
    vi.stubEnv('VITE_API_URL', '')
    globalThis.window.__ENV__ = {
      VITE_USE_AUTH_API: 'true',
    }

    expect(() =>
      ServiceFactory.getInstance({
        logger: createNoopLogger(),
      })
    ).not.toThrow()
  })
})
