export type UiMessageVariant = 'info' | 'success' | 'warning' | 'error'

export type UiMessage = {
  id: string
  variant: UiMessageVariant
  title?: string
  description: string
  details?: string
  createdAt: number
  /**
   * Auto dismiss the message after this many milliseconds.
   * Useful for confirmation-style success messages.
   */
  autoDismissMs?: number
  /**
   * Dismiss the message on the next user interaction (pointer/keyboard).
   * Useful to avoid lingering confirmations without requiring a manual close.
   */
  dismissOnNextAction?: boolean
}
