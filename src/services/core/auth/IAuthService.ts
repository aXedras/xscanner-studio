import type { AuthResult, AuthSessionResult, SignInInput, SignUpInput } from './types'

export interface IAuthService {
  signIn(input: SignInInput): Promise<AuthResult>
  signUp(input: SignUpInput): Promise<AuthResult>
  signOut(): Promise<void>
  getSession(): Promise<AuthSessionResult>
}
