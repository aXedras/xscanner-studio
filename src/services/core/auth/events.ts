export const AUTH_SESSION_CHANGED_EVENT = 'xscanner:auth-session-changed'

export function emitAuthSessionChanged(): void {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new Event(AUTH_SESSION_CHANGED_EVENT))
}
