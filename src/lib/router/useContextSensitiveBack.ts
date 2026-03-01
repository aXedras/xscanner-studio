import { useCallback, useContext } from 'react'
import { useNavigate } from 'react-router-dom'
import { NavigationHistoryContext } from './NavigationHistoryContext'

export function useContextSensitiveBack(fallbackPath = '/') {
  const navigate = useNavigate()
  const history = useContext(NavigationHistoryContext)

  return useCallback(() => {
    const target = history?.popPreviousPath() ?? null
    if (target) {
      navigate(target)
      return
    }

    // If we do not know the previous in-app route, prefer a safe in-app fallback.
    if (window.history.length > 1) {
      navigate(-1)
      return
    }

    navigate(fallbackPath)
  }, [fallbackPath, history, navigate])
}
