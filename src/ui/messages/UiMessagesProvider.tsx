import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { UiMessagesContext, type UiMessagesApi } from './UiMessagesContext'
import type { UiMessage } from './types'

const createId = (): string => {
  // Stable enough for client-only UI state.
  return `${Date.now()}_${Math.random().toString(16).slice(2)}`
}

export function UiMessagesProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<UiMessage[]>([])
  const timersRef = useRef<Map<string, number>>(new Map())

  const push: UiMessagesApi['push'] = useCallback(input => {
    const isSuccess = input.variant === 'success'
    const isError = input.variant === 'error'

    const next: UiMessage = {
      id: createId(),
      variant: input.variant,
      title: input.title,
      description: input.description,
      details: input.details,
      createdAt: Date.now(),
      autoDismissMs: input.autoDismissMs ?? (isSuccess ? 5000 : undefined),
      dismissOnNextAction: input.dismissOnNextAction ?? (isError ? true : undefined),
    }

    setMessages(prev => [...prev, next])
  }, [])

  const dismiss: UiMessagesApi['dismiss'] = useCallback(id => {
    setMessages(prev => prev.filter(message => message.id !== id))
  }, [])

  const clear: UiMessagesApi['clear'] = useCallback(() => {
    setMessages([])
  }, [])

  const value = useMemo<UiMessagesApi>(() => ({ messages, push, dismiss, clear }), [messages, push, dismiss, clear])

  useEffect(() => {
    // Schedule auto-dismiss timers.
    for (const message of messages) {
      if (!message.autoDismissMs) continue
      if (timersRef.current.has(message.id)) continue

      const handle = window.setTimeout(() => {
        timersRef.current.delete(message.id)
        setMessages(prev => prev.filter(m => m.id !== message.id))
      }, message.autoDismissMs)

      timersRef.current.set(message.id, handle)
    }

    // Clean up timers for messages that were dismissed early.
    const ids = new Set(messages.map(m => m.id))
    for (const [id, handle] of timersRef.current.entries()) {
      if (ids.has(id)) continue
      window.clearTimeout(handle)
      timersRef.current.delete(id)
    }
  }, [messages])

  useEffect(() => {
    const timers = timersRef.current

    return () => {
      for (const handle of timers.values()) {
        window.clearTimeout(handle)
      }
      timers.clear()
    }
  }, [])

  useEffect(() => {
    const shouldDismissOnNextAction = messages.some(m => m.dismissOnNextAction)
    if (!shouldDismissOnNextAction) return

    const options: AddEventListenerOptions = { capture: true }

    const isMessageCenterInteraction = (event: Event): boolean => {
      const containers = Array.from(document.querySelectorAll('[data-ui-message-center="true"]'))
      if (containers.length === 0) return false

      const target = event.target
      if (!(target instanceof Node)) return false

      return containers.some(container => container.contains(target))
    }

    const dismissOnAction = (event: Event) => {
      if (isMessageCenterInteraction(event)) return
      setMessages(prev => prev.filter(m => !m.dismissOnNextAction))
      window.removeEventListener('pointerdown', dismissOnAction, options)
      window.removeEventListener('keydown', dismissOnAction, options)
    }

    // Any user action should clear success confirmations.
    window.addEventListener('pointerdown', dismissOnAction, options)
    window.addEventListener('keydown', dismissOnAction, options)

    return () => {
      window.removeEventListener('pointerdown', dismissOnAction, options)
      window.removeEventListener('keydown', dismissOnAction, options)
    }
  }, [messages])

  return <UiMessagesContext.Provider value={value}>{children}</UiMessagesContext.Provider>
}
