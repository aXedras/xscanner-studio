import type { ILogger } from '../../../../lib/utils/logging'
import type { HttpJsonClient } from '../../../infrastructure/http/httpClient'
import type { IAuthService } from '../IAuthService'
import { emitAuthSessionChanged } from '../events'
import type { AuthResult, AuthSessionResult, SignInInput, SignUpInput } from '../types'

export class AuthService implements IAuthService {
  declare private readonly client: HttpJsonClient
  declare private readonly logger: ILogger

  constructor(input: { client: HttpJsonClient; logger: ILogger }) {
    this.client = input.client
    this.logger = input.logger
  }

  private async signInWithPassword(input: SignInInput): Promise<AuthResult> {
    const email = input.email.trim()
    this.logger.info('AuthService', 'signInWithPassword via API', { hasEmail: Boolean(email) })
    return await this.client.postJson<AuthResult>('/api/v1/auth/sign-in', {
      email,
      password: input.password,
    })
  }

  private async signUpWithPassword(input: SignUpInput): Promise<AuthResult> {
    const email = input.email.trim()
    const displayName = input.displayName.trim()
    this.logger.info('AuthService', 'signUpWithPassword via API', {
      hasEmail: Boolean(email),
      hasDisplayName: Boolean(displayName),
    })
    return await this.client.postJson<AuthResult>('/api/v1/auth/sign-up', {
      email,
      password: input.password,
      displayName,
    })
  }

  private async signOutRequest(): Promise<void> {
    this.logger.info('AuthService', 'signOut via API')
    await this.client.postJson('/api/v1/auth/sign-out', {})
  }

  private async getSessionRequest(): Promise<AuthSessionResult> {
    this.logger.info('AuthService', 'getSession via API')
    return await this.client.getJson<AuthSessionResult>('/api/v1/auth/session')
  }

  async signIn(input: SignInInput): Promise<AuthResult> {
    this.logger.info('AuthService', 'signIn')

    try {
      const result = await this.signInWithPassword(input)
      emitAuthSessionChanged()
      return result
    } catch (error) {
      this.logger.error('AuthService', 'signIn failed', error)
      throw error
    }
  }

  async signUp(input: SignUpInput): Promise<AuthResult> {
    this.logger.info('AuthService', 'signUp', {
      hasDisplayName: Boolean(input.displayName?.trim()),
    })

    if (!input.displayName.trim()) {
      const error = new Error('Display name is required')
      this.logger.warn('AuthService', 'signUp validation failed', { message: error.message })
      throw error
    }

    try {
      const result = await this.signUpWithPassword({
        ...input,
        displayName: input.displayName.trim(),
      })
      emitAuthSessionChanged()
      return result
    } catch (error) {
      this.logger.error('AuthService', 'signUp failed', error)
      throw error
    }
  }

  async signOut(): Promise<void> {
    this.logger.info('AuthService', 'signOut')

    try {
      await this.signOutRequest()
      emitAuthSessionChanged()
    } catch (error) {
      this.logger.error('AuthService', 'signOut failed', error)
      throw error
    }
  }

  async getSession(): Promise<AuthSessionResult> {
    this.logger.info('AuthService', 'getSession')

    try {
      return await this.getSessionRequest()
    } catch (error) {
      this.logger.error('AuthService', 'getSession failed', error)
      throw error
    }
  }
}
