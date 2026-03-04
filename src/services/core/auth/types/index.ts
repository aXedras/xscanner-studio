export interface SignInInput {
  email: string
  password: string
}

export interface SignUpInput {
  email: string
  password: string
  displayName: string
}

export interface AuthResult {
  // Backend may return a session immediately, or null when email confirmation is required.
  hasSession: boolean
}

export interface AuthSessionUser {
  id: string
  email: string | null
  user_metadata?: {
    display_name?: string | null
  }
}

export interface AuthSessionResult {
  session: AuthSessionUser | null
}
