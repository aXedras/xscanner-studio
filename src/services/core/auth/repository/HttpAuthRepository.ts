import type { ILogger } from '../../../../lib/utils/logging'
import type { HttpJsonClient } from '../../../infrastructure/http/httpClient'
import type { AuthResult, AuthSessionResult, SignInInput, SignUpInput } from '../types'
import type { IAuthRepository } from './IAuthRepository'

export class HttpAuthRepository implements IAuthRepository {
  declare private readonly client: HttpJsonClient
  declare private readonly logger: ILogger

  constructor(input: { client: HttpJsonClient; logger: ILogger }) {
    this.client = input.client
    this.logger = input.logger
  }

  async signInWithPassword(input: SignInInput): Promise<AuthResult> {
    const email = input.email.trim()
    this.logger.info('HttpAuthRepository', 'signInWithPassword via API', { hasEmail: Boolean(email) })

    return await this.client.postJson<AuthResult>('/api/v1/auth/sign-in', {
      email,
      password: input.password,
    })
  }

  async signUpWithPassword(input: SignUpInput): Promise<AuthResult> {
    const email = input.email.trim()
    const displayName = input.displayName.trim()

    this.logger.info('HttpAuthRepository', 'signUpWithPassword via API', {
      hasEmail: Boolean(email),
      hasDisplayName: Boolean(displayName),
    })

    return await this.client.postJson<AuthResult>('/api/v1/auth/sign-up', {
      email,
      password: input.password,
      displayName,
    })
  }

  async signOut(): Promise<void> {
    this.logger.info('HttpAuthRepository', 'signOut via API')
    await this.client.postJson('/api/v1/auth/sign-out', {})
  }

  async getSession(): Promise<AuthSessionResult> {
    this.logger.info('HttpAuthRepository', 'getSession via API')
    return await this.client.getJson<AuthSessionResult>('/api/v1/auth/session')
  }
}
