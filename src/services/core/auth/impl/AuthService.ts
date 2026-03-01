import type { ILogger } from '../../../../lib/utils/logging'
import type { IAuthService } from '../IAuthService'
import type { IAuthRepository } from '../repository/IAuthRepository'
import type { AuthResult, SignInInput, SignUpInput } from '../types'

export class AuthService implements IAuthService {
  declare private readonly authRepository: IAuthRepository
  declare private readonly logger: ILogger

  constructor(authRepository: IAuthRepository, logger: ILogger) {
    this.authRepository = authRepository
    this.logger = logger
  }

  async signIn(input: SignInInput): Promise<AuthResult> {
    this.logger.info('AuthService', 'signIn')

    try {
      return await this.authRepository.signInWithPassword(input)
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
      return await this.authRepository.signUpWithPassword({
        ...input,
        displayName: input.displayName.trim(),
      })
    } catch (error) {
      this.logger.error('AuthService', 'signUp failed', error)
      throw error
    }
  }

  async signOut(): Promise<void> {
    this.logger.info('AuthService', 'signOut')

    try {
      await this.authRepository.signOut()
    } catch (error) {
      this.logger.error('AuthService', 'signOut failed', error)
      throw error
    }
  }
}
