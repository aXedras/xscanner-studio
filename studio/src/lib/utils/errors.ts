import type { TFunction } from 'i18next'

export type AppErrorCode =
  | 'AUTH_INVALID_CREDENTIALS'
  | 'AUTH_EMAIL_NOT_CONFIRMED'
  | 'AUTH_USER_ALREADY_EXISTS'
  | 'AUTH_WEAK_PASSWORD'
  | 'AUTH_TOO_MANY_REQUESTS'
  | 'NETWORK_ERROR'
  | 'UNKNOWN'

export type AppError = {
  code: AppErrorCode
  status?: number
  rawMessage?: string
}

type ErrorLike = {
  name?: unknown
  message?: unknown
  status?: unknown
  statusCode?: unknown
}

const toErrorLike = (error: unknown): ErrorLike | null => {
  if (!error || typeof error !== 'object') return null
  return error as ErrorLike
}

const getStringMessage = (error: unknown): string | undefined => {
  if (typeof error === 'string') return error
  if (error instanceof Error) return error.message

  const errorLike = toErrorLike(error)
  if (errorLike && typeof errorLike.message === 'string') return errorLike.message

  return undefined
}

const getNumberStatus = (error: unknown): number | undefined => {
  const errorLike = toErrorLike(error)
  if (!errorLike) return undefined
  // Supabase (Storage) often uses `statusCode` (sometimes as string).
  if (typeof errorLike.statusCode === 'number') return errorLike.statusCode
  if (typeof errorLike.statusCode === 'string') {
    const parsed = Number(errorLike.statusCode)
    if (Number.isFinite(parsed)) return parsed
  }

  if (typeof errorLike.status === 'number') return errorLike.status
  if (typeof errorLike.status === 'string') {
    const parsed = Number(errorLike.status)
    return Number.isFinite(parsed) ? parsed : undefined
  }
  return undefined
}

const isNetworkError = (error: unknown, message: string | undefined): boolean => {
  // Fetch failures are commonly TypeError in browsers.
  if (error instanceof TypeError) {
    if (!message) return true
    return /failed to fetch|networkerror|load failed|network request failed/i.test(message)
  }

  return Boolean(message && /failed to fetch|networkerror|load failed|network request failed/i.test(message))
}

const isAuthErrorMessage = (message: string, needle: RegExp): boolean => {
  return needle.test(message)
}

export function normalizeError(error: unknown): AppError {
  const rawMessage = getStringMessage(error)
  const status = getNumberStatus(error)

  if (isNetworkError(error, rawMessage)) {
    return {
      code: 'NETWORK_ERROR',
      status,
      rawMessage,
    }
  }

  if (typeof rawMessage === 'string') {
    if (status === 401 && isAuthErrorMessage(rawMessage, /invalid login credentials/i)) {
      return {
        code: 'AUTH_INVALID_CREDENTIALS',
        status,
        rawMessage,
      }
    }

    if (isAuthErrorMessage(rawMessage, /email not confirmed/i)) {
      return {
        code: 'AUTH_EMAIL_NOT_CONFIRMED',
        status,
        rawMessage,
      }
    }

    if (isAuthErrorMessage(rawMessage, /user already registered|already registered/i)) {
      return {
        code: 'AUTH_USER_ALREADY_EXISTS',
        status,
        rawMessage,
      }
    }

    if (isAuthErrorMessage(rawMessage, /password should be at least|weak password|too weak/i)) {
      return {
        code: 'AUTH_WEAK_PASSWORD',
        status,
        rawMessage,
      }
    }

    if (status === 429 || isAuthErrorMessage(rawMessage, /too many requests|rate limit/i)) {
      return {
        code: 'AUTH_TOO_MANY_REQUESTS',
        status,
        rawMessage,
      }
    }
  }

  return {
    code: 'UNKNOWN',
    status,
    rawMessage,
  }
}

export function getUserFacingErrorMessage(t: TFunction, error: unknown): string {
  const appError = normalizeError(error)

  switch (appError.code) {
    case 'AUTH_INVALID_CREDENTIALS':
      return t('auth.errors.invalidCredentials')
    case 'AUTH_EMAIL_NOT_CONFIRMED':
      return t('auth.errors.emailNotConfirmed')
    case 'AUTH_USER_ALREADY_EXISTS':
      return t('auth.errors.userAlreadyExists')
    case 'AUTH_WEAK_PASSWORD':
      return t('auth.errors.weakPassword')
    case 'AUTH_TOO_MANY_REQUESTS':
      return t('auth.errors.tooManyRequests')
    case 'NETWORK_ERROR':
      return t('common.error.network')
    case 'UNKNOWN':
    default:
      if (appError.status === 401) return t('common.error.unauthorized')
      if (appError.status === 403) return t('common.error.forbidden')
      if (appError.status === 404) return t('common.error.notFound')
      if (typeof appError.status === 'number' && appError.status >= 500) return t('common.error.server')
      return t('common.error.unknown')
  }
}
