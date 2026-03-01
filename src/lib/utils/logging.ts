/**
 * Logging abstraction for xScanner Studio
 *
 * Usage:
 * import { logger } from '@/lib/utils/logging'
 * logger.debug('Component', 'Message', { context })
 *
 * Configuration via .env:
 * VITE_LOG_LEVEL=debug|info|warn|error|none
 */

export type LogLevel = 'debug' | 'info' | 'warn' | 'error' | 'none'

export interface ILogger {
  debug(category: string, message: string, data?: unknown): void
  info(category: string, message: string, data?: unknown): void
  warn(category: string, message: string, data?: unknown): void
  error(category: string, message: string, error?: unknown): void
  time(label: string): void
  timeEnd(label: string): void
  group(category: string, label: string): void
  groupEnd(): void
}

type LogPayload = {
  level: LogLevel
  category: string
  message: string
  data?: unknown
}

const getRuntimeEnv = (key: string): string | undefined => {
  if (typeof window === 'undefined') return undefined
  const value = window.__ENV__?.[key]
  const trimmed = (value || '').trim()
  return trimmed ? trimmed : undefined
}

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

const shouldShipToFile = (): boolean => {
  const value = getRuntimeEnv('VITE_LOG_TO_FILE') || (import.meta.env.VITE_LOG_TO_FILE as string)
  return Boolean(import.meta.env.DEV) && value === 'true'
}

const getIngestPath = (): string => {
  return getRuntimeEnv('VITE_LOG_INGEST_PATH') || (import.meta.env.VITE_LOG_INGEST_PATH as string) || '/__studio_log'
}

const shipToFile = (payload: LogPayload): void => {
  if (!shouldShipToFile()) return

  try {
    const body = JSON.stringify({
      ...payload,
      data: payload.data === undefined ? undefined : redactSensitive(payload.data),
    })

    const url = getIngestPath()

    // Prefer sendBeacon for non-blocking background delivery.
    if (typeof navigator !== 'undefined' && typeof navigator.sendBeacon === 'function') {
      navigator.sendBeacon(url, new Blob([body], { type: 'application/json' }))
      return
    }

    void fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
      keepalive: true,
    })
  } catch {
    // Never throw from logging.
  }
}

class Logger implements ILogger {
  private level: LogLevel
  private enabledCategories: Set<string> | null

  constructor() {
    this.level = this.getLogLevel()
    this.enabledCategories = this.getEnabledCategories()
  }

  private getLogLevel(): LogLevel {
    const level = (getRuntimeEnv('VITE_LOG_LEVEL') as LogLevel) || (import.meta.env.VITE_LOG_LEVEL as LogLevel)
    return level || (import.meta.env.DEV ? 'debug' : 'error')
  }

  private getEnabledCategories(): Set<string> | null {
    const categories = getRuntimeEnv('VITE_LOG_CATEGORIES') || (import.meta.env.VITE_LOG_CATEGORIES as string)
    if (!categories) return null
    return new Set(categories.split(',').map(c => c.trim()))
  }

  private shouldLog(level: LogLevel, category: string): boolean {
    // Check level hierarchy
    const levels: LogLevel[] = ['debug', 'info', 'warn', 'error', 'none']
    const currentLevelIndex = levels.indexOf(this.level)
    const messageLevelIndex = levels.indexOf(level)

    if (currentLevelIndex > messageLevelIndex) return false
    if (this.level === 'none') return false

    // Check category filter
    if (this.enabledCategories && !this.enabledCategories.has(category)) {
      return false
    }

    return true
  }

  private formatMessage(category: string, message: string): string {
    return `[${category}] ${message}`
  }

  debug(category: string, message: string, data?: unknown): void {
    if (!this.shouldLog('debug', category)) return
    console.debug(this.formatMessage(category, message), data ?? '')
    shipToFile({ level: 'debug', category, message, data })
  }

  info(category: string, message: string, data?: unknown): void {
    if (!this.shouldLog('info', category)) return
    console.info(this.formatMessage(category, message), data ?? '')
    shipToFile({ level: 'info', category, message, data })
  }

  warn(category: string, message: string, data?: unknown): void {
    if (!this.shouldLog('warn', category)) return
    console.warn(this.formatMessage(category, message), data ?? '')
    shipToFile({ level: 'warn', category, message, data })
  }

  error(category: string, message: string, error?: unknown): void {
    if (!this.shouldLog('error', category)) return
    console.error(this.formatMessage(category, message), error ?? '')
    shipToFile({ level: 'error', category, message, data: error })
  }

  time(label: string): void {
    if (this.level === 'none') return
    console.time(`⏱️ ${label}`)
  }

  timeEnd(label: string): void {
    if (this.level === 'none') return
    console.timeEnd(`⏱️ ${label}`)
  }

  group(category: string, label: string): void {
    if (this.level === 'none') return
    console.group(this.formatMessage(category, label))
  }

  groupEnd(): void {
    if (this.level === 'none') return
    console.groupEnd()
  }
}

// Singleton instance
export const logger = new Logger()
