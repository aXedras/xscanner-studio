import type { PagedResult } from '../persistence/query'

type RawPagedResponse<T> = {
  items: T[]
  total: number
  page: number
  page_size: number
}

function assertFiniteNumber(value: unknown, fieldName: string, context: string): number {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    throw new TypeError(`${context} is invalid: expected numeric field '${fieldName}'.`)
  }
  return value
}

export function toPagedResult<T>(response: RawPagedResponse<T>, context: string): PagedResult<T> {
  if (!Array.isArray(response.items)) {
    throw new TypeError(`${context} is invalid: expected array field 'items'.`)
  }

  const total = assertFiniteNumber(response.total, 'total', context)
  const page = assertFiniteNumber(response.page, 'page', context)
  const pageSize = assertFiniteNumber(response.page_size, 'page_size', context)

  return {
    items: response.items,
    total,
    page,
    pageSize,
  }
}
