import { useCallback, useEffect, useMemo, useRef, type ReactNode } from 'react'
import { useLocation } from 'react-router-dom'
import { NavigationHistoryContext, type NavigationHistory } from './NavigationHistoryContext'

const toPath = (input: { pathname: string; search: string; hash: string }): string => {
  return `${input.pathname}${input.search}${input.hash}`
}

export function NavigationHistoryProvider({ children }: { children: ReactNode }) {
  const location = useLocation()
  const stackRef = useRef<string[]>([])

  useEffect(() => {
    const nextPath = toPath(location)
    const stack = stackRef.current
    const last = stack[stack.length - 1]

    if (last !== nextPath) {
      stack.push(nextPath)
      if (stack.length > 50) stack.shift()
    }
  }, [location])

  const popPreviousPath = useCallback((): string | null => {
    const stack = stackRef.current
    if (stack.length <= 1) return null

    // Remove current.
    stack.pop()
    const target = stack[stack.length - 1] ?? null
    return target
  }, [])

  const value = useMemo<NavigationHistory>(() => ({ popPreviousPath }), [popPreviousPath])

  return <NavigationHistoryContext.Provider value={value}>{children}</NavigationHistoryContext.Provider>
}
