import { useCallback, useEffect, useMemo, useLayoutEffect, useRef } from 'react'
import type { ExtractionsPageState } from './useExtractionsPageState'

type StoredStateV1 = {
  v: 1
  savedAt: number
  scrollY: number
  state: ExtractionsPageState
}

type Args = {
  storageKey: string
  state: ExtractionsPageState
  initialScrollY?: number | null
  restoreScrollWhen?: boolean
  skipScrollRestore?: boolean
}

function isStoredStateV1(value: unknown): value is StoredStateV1 {
  if (!value || typeof value !== 'object') return false
  const v = value as Partial<StoredStateV1>
  if (v.v !== 1) return false
  if (typeof v.savedAt !== 'number') return false
  if (typeof v.scrollY !== 'number') return false
  if (!v.state || typeof v.state !== 'object') return false
  return true
}

export function useExtractionsPagePersistence({
  storageKey,
  state,
  initialScrollY,
  restoreScrollWhen,
  skipScrollRestore,
}: Args) {
  const stateRef = useRef<ExtractionsPageState>(state)
  const scrollYRef = useRef<number>(0)

  useLayoutEffect(() => {
    stateRef.current = state
  }, [state])

  const scrollRafRef = useRef<number | null>(null)
  useEffect(() => {
    if (skipScrollRestore) return

    const onScroll = () => {
      if (scrollRafRef.current != null) return
      scrollRafRef.current = window.requestAnimationFrame(() => {
        scrollRafRef.current = null
        scrollYRef.current = window.scrollY
      })
    }

    scrollYRef.current = window.scrollY
    window.addEventListener('scroll', onScroll, { passive: true })

    return () => {
      window.removeEventListener('scroll', onScroll)
      if (scrollRafRef.current != null) window.cancelAnimationFrame(scrollRafRef.current)
      scrollRafRef.current = null
    }
  }, [skipScrollRestore])

  const pendingScrollYRef = useRef<number | null>(null)
  const restoredRef = useRef(false)

  useEffect(() => {
    if (skipScrollRestore) return
    if (typeof initialScrollY !== 'number') return
    pendingScrollYRef.current = initialScrollY
  }, [initialScrollY, skipScrollRestore])

  const save = useMemo(() => {
    return () => {
      try {
        const payload: StoredStateV1 = {
          v: 1,
          savedAt: Date.now(),
          scrollY: scrollYRef.current,
          state: stateRef.current,
        }
        sessionStorage.setItem(storageKey, JSON.stringify(payload))
      } catch {
        // ignore persistence failures (e.g. private mode / quota)
      }
    }
  }, [storageKey])

  const saveNow = useCallback(() => {
    save()
  }, [save])

  useEffect(() => {
    // Persist on every state change so back-navigation restores page/filters reliably.
    saveNow()
  }, [saveNow, state])

  useEffect(() => {
    return () => saveNow()
  }, [saveNow])

  useEffect(() => {
    if (skipScrollRestore) return
    if (restoredRef.current) return

    const shouldRestore = restoreScrollWhen ?? true
    if (!shouldRestore) return

    const scrollY = pendingScrollYRef.current
    if (scrollY == null) return

    restoredRef.current = true
    pendingScrollYRef.current = null

    requestAnimationFrame(() => {
      window.scrollTo({ top: scrollY, left: 0, behavior: 'auto' })
    })
  }, [restoreScrollWhen, skipScrollRestore])
}

export function loadExtractionsPagePersistedState(
  storageKey: string
): { state: ExtractionsPageState; scrollY: number } | null {
  if (typeof sessionStorage === 'undefined') return null
  try {
    const raw = sessionStorage.getItem(storageKey)
    if (!raw) return null
    const parsed: unknown = JSON.parse(raw)
    if (!isStoredStateV1(parsed)) return null
    return { state: parsed.state, scrollY: parsed.scrollY }
  } catch {
    return null
  }
}
