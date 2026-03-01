import { createContext, useContext } from 'react'
import type { UiMessage, UiMessageVariant } from './types'

export type UiMessagesApi = {
  messages: UiMessage[]
  push: (input: {
    variant: UiMessageVariant
    title?: string
    description: string
    details?: string
    autoDismissMs?: number
    dismissOnNextAction?: boolean
  }) => void
  dismiss: (id: string) => void
  clear: () => void
}

export const UiMessagesContext = createContext<UiMessagesApi | null>(null)

export function useUiMessages(): UiMessagesApi {
  const context = useContext(UiMessagesContext)
  if (!context) {
    throw new Error('useUiMessages must be used within UiMessagesProvider')
  }
  return context
}
