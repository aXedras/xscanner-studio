import { createContext } from 'react'

export type NavigationHistory = {
  popPreviousPath: () => string | null
}

export const NavigationHistoryContext = createContext<NavigationHistory | null>(null)
