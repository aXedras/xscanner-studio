import type { SupabaseClient } from '@supabase/supabase-js'
import type { ILogger } from '../../../../lib/utils/logging'
import type { AuthResult, SignInInput, SignUpInput } from '../types'
import type { IAuthRepository } from './IAuthRepository'
import { logSupabaseFailure } from '../../../infrastructure/persistence/supabaseErrors'

export class SupabaseAuthRepository implements IAuthRepository {
  declare private readonly supabase: SupabaseClient
  declare private readonly logger: ILogger

  constructor(supabase: SupabaseClient, logger: ILogger) {
    this.supabase = supabase
    this.logger = logger
  }

  private logFailure(operation: string, error: unknown): void {
    logSupabaseFailure(this.logger, 'SupabaseAuthRepository', operation, error, { warnOn4xx: true })
  }

  async signInWithPassword(input: SignInInput): Promise<AuthResult> {
    const { email, password } = input

    this.logger.info('SupabaseAuthRepository', 'signInWithPassword', {
      hasEmail: Boolean(email),
    })

    const { data, error } = await this.supabase.auth.signInWithPassword({
      email,
      password,
    })

    if (error) {
      this.logFailure('signInWithPassword failed', error)
      throw error
    }

    return { hasSession: Boolean(data.session) }
  }

  async signUpWithPassword(input: SignUpInput): Promise<AuthResult> {
    const { email, password, displayName } = input

    this.logger.info('SupabaseAuthRepository', 'signUpWithPassword', {
      hasEmail: Boolean(email),
      hasDisplayName: Boolean(displayName?.trim()),
    })

    const { data, error } = await this.supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          display_name: displayName,
        },
      },
    })

    if (error) {
      this.logFailure('signUpWithPassword failed', error)
      throw error
    }

    return { hasSession: Boolean(data.session) }
  }

  async signOut(): Promise<void> {
    this.logger.info('SupabaseAuthRepository', 'signOut')

    const { error } = await this.supabase.auth.signOut()

    if (error) {
      this.logFailure('signOut failed', error)
      throw error
    }
  }
}
