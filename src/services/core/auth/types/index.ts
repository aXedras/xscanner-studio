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
  // Supabase may return a session immediately, or null when email confirmation is required.
  hasSession: boolean
}
