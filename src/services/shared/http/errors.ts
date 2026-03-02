import { HttpError } from '../../infrastructure/http/httpClient'

export function isHttpNotFound(error: unknown): boolean {
  return error instanceof HttpError && error.kind === 'http' && error.status === 404
}
