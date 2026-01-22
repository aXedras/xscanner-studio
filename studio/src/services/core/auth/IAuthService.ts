import type { AuthResult, SignInInput, SignUpInput } from './types'

export interface IAuthService {
  signIn(input: SignInInput): Promise<AuthResult>
  signUp(input: SignUpInput): Promise<AuthResult>
  signOut(): Promise<void>
}
