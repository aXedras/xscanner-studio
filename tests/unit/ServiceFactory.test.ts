import { afterEach, beforeEach, describe, expect, test } from 'vitest'

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
  })

  afterEach(() => {
    resetServiceFactorySingleton()
    globalThis.window.__ENV__ = {}
  })

  test('throws when API adapter is enabled but VITE_API_URL is missing', () => {
    globalThis.window.__ENV__ = {
      VITE_USE_AUTH_API: 'true',
    }

    expect(() =>
      ServiceFactory.getInstance({
        supabase: {} as never,
        logger: createNoopLogger(),
      })
    ).toThrow('VITE_API_URL is required when API adapters are enabled.')
  })
})
