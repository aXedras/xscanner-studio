import type { ILogger } from '../../../lib/utils/logging'

/**
 * Extract an HTTP-like status code from Supabase errors (when available).
 *
 * Supabase errors are not guaranteed to share a single shape across modules
 * (`supabase.auth.*` vs `from(table)`), so we treat this defensively.
 */
export function getSupabaseErrorStatus(error: unknown): number | undefined {
  if (typeof error !== 'object' || error === null) return undefined
  const maybeStatus = (error as { status?: unknown }).status
  return typeof maybeStatus === 'number' ? maybeStatus : undefined
}

/**
 * Standardized logging for Supabase failures.
 *
 * Motivation:
 * - Keep logging consistent across repositories.
 * - Avoid copy/pasting "extract status" logic and ad-hoc severity rules.
 *
 * Options:
 * - `warnOn4xx`: if enabled, 4xx errors are logged at WARN (often user-caused),
 *   while other errors are logged at ERROR.
 */
export function logSupabaseFailure(
  logger: ILogger,
  repoName: string,
  operation: string,
  error: unknown,
  options?: { warnOn4xx?: boolean }
): void {
  const status = getSupabaseErrorStatus(error)

  if (options?.warnOn4xx && status && status >= 400 && status < 500) {
    logger.warn(repoName, operation, {
      status,
      message: error instanceof Error ? error.message : String(error),
    })
    return
  }

  logger.error(repoName, operation, error)
}
