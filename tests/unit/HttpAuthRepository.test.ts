import { describe, expect, test, vi } from 'vitest'

import type { HttpJsonClient } from '../../src/services/infrastructure/http/httpClient'
import { HttpAuthRepository } from '../../src/services/core/auth/repository/HttpAuthRepository'

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

describe('HttpAuthRepository', () => {
  test('posts sign-in payload and returns auth result', async () => {
    const client = createClient()
    const logger = createLogger()
    client.postJson.mockResolvedValueOnce({ hasSession: true })

    const repository = new HttpAuthRepository({ client, logger })
    const result = await repository.signInWithPassword({
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

    const repository = new HttpAuthRepository({ client, logger })
    const result = await repository.signUpWithPassword({
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

  test('posts sign-out request', async () => {
    const client = createClient()
    const logger = createLogger()
    client.postJson.mockResolvedValueOnce(undefined)

    const repository = new HttpAuthRepository({ client, logger })
    await repository.signOut()

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

    const repository = new HttpAuthRepository({ client, logger })
    const result = await repository.getSession()

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
