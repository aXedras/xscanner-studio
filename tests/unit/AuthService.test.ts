import { describe, expect, test, vi } from 'vitest'

import type { HttpJsonClient } from '../../src/services/infrastructure/http/httpClient'
import { AuthService } from '../../src/services/core/auth/impl/AuthService'
import { AUTH_SESSION_CHANGED_EVENT } from '../../src/services/core/auth/events'

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

describe('AuthService', () => {
  test('posts sign-in payload and returns auth result', async () => {
    const client = createClient()
    const logger = createLogger()
    client.postJson.mockResolvedValueOnce({ hasSession: true })

    const service = new AuthService({ client, logger })
    const result = await service.signIn({
      email: ' user@example.com ',
      password: 'secret',
    })

    expect(client.postJson).toHaveBeenCalledWith('/api/v1/auth/sign-in', {
      email: 'user@example.com',
      password: 'secret',
    })
    expect(result).toEqual({ hasSession: true })
  })

  test('posts sign-up payload with trimmed display name and returns auth result', async () => {
    const client = createClient()
    const logger = createLogger()
    client.postJson.mockResolvedValueOnce({ hasSession: false })

    const service = new AuthService({ client, logger })
    const result = await service.signUp({
      email: 'person@example.com',
      password: 'secret',
      displayName: '  Jane Doe  ',
    })

    expect(client.postJson).toHaveBeenCalledWith('/api/v1/auth/sign-up', {
      email: 'person@example.com',
      password: 'secret',
      displayName: 'Jane Doe',
    })
    expect(result).toEqual({ hasSession: false })
  })

  test('emits auth session changed event after successful sign-in even when hasSession is false', async () => {
    const client = createClient()
    const logger = createLogger()
    client.postJson.mockResolvedValueOnce({ hasSession: false })
    const dispatchSpy = vi.spyOn(globalThis, 'dispatchEvent')

    const service = new AuthService({ client, logger })
    await service.signIn({
      email: 'user@example.com',
      password: 'secret',
    })

    expect(dispatchSpy).toHaveBeenCalledWith(expect.objectContaining({ type: AUTH_SESSION_CHANGED_EVENT }))
  })

  test('posts sign-out request', async () => {
    const client = createClient()
    const logger = createLogger()
    client.postJson.mockResolvedValueOnce(undefined)

    const service = new AuthService({ client, logger })
    await service.signOut()

    expect(client.postJson).toHaveBeenCalledWith('/api/v1/auth/sign-out', {})
  })

  test('gets auth session snapshot via API', async () => {
    const client = createClient()
    const logger = createLogger()
    client.getJson.mockResolvedValueOnce({
      session: {
        id: 'user-1',
        email: 'user@example.com',
        user_metadata: { display_name: 'User One' },
      },
    })

    const service = new AuthService({ client, logger })
    const result = await service.getSession()

    expect(client.getJson).toHaveBeenCalledWith('/api/v1/auth/session')
    expect(result).toEqual({
      session: {
        id: 'user-1',
        email: 'user@example.com',
        user_metadata: { display_name: 'User One' },
      },
    })
  })
})
