import type { TFunction } from 'i18next'
import { getUserFacingErrorMessage } from '../../lib/utils/errors'
import type { UiMessage } from './types'

const redactSensitive = (value: unknown): unknown => {
  if (!value || typeof value !== 'object') return value
  if (Array.isArray(value)) return value.map(redactSensitive)

  const result: Record<string, unknown> = {}
  for (const [key, child] of Object.entries(value as Record<string, unknown>)) {
    if (/password|token|secret|api[_-]?key|anon[_-]?key/i.test(key)) {
      result[key] = '[REDACTED]'
      continue
    }
    result[key] = redactSensitive(child)
  }
  return result
}

const safeStringify = (value: unknown): string | null => {
  try {
    return JSON.stringify(redactSensitive(value), null, 2)
  } catch {
    return null
  }
}

const getErrorDetails = (error: unknown): string | undefined => {
  // Prefer explicit details property if present.
  if (error && typeof error === 'object' && 'details' in error) {
    const d = (error as { details?: unknown }).details
    if (typeof d === 'string' && d.trim()) return d
  }

  if (error instanceof Error) {
    const payload = {
      name: error.name,
      message: error.message,
      stack: error.stack,
      ...(error as unknown as Record<string, unknown>),
    }
    const json = safeStringify(payload)
    if (!json) return undefined
    return json.length > 4000 ? `${json.slice(0, 4000)}\n…(truncated)` : json
  }

  const json = safeStringify(error)
  if (!json) return undefined
  return json.length > 4000 ? `${json.slice(0, 4000)}\n…(truncated)` : json
}

export const createErrorMessage = (t: TFunction, error: unknown): Omit<UiMessage, 'id' | 'createdAt'> => {
  return {
    variant: 'error',
    title: t('common.toast.error.title'),
    description: getUserFacingErrorMessage(t, error),
    details: getErrorDetails(error),
  }
}
