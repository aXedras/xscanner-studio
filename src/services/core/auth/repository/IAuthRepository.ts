import type { AuthResult, AuthSessionResult, SignInInput, SignUpInput } from '../types'

export interface IAuthRepository {
  signInWithPassword(input: SignInInput): Promise<AuthResult>
  signUpWithPassword(input: SignUpInput): Promise<AuthResult>
  signOut(): Promise<void>
  getSession(): Promise<AuthSessionResult>
}
