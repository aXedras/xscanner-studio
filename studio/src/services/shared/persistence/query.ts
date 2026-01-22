export type SortDirection = 'asc' | 'desc'

export type SortSpec<Field extends string> = {
  field: Field
  direction: SortDirection
}

export type PageSpec = {
  page: number
  pageSize: number
}

export type DateRangeSpec = {
  from?: string
  to?: string
}

export type PagedResult<T> = {
  items: T[]
  total: number
  page: number
  pageSize: number
}

export function normalizePageSpec(spec: PageSpec): PageSpec {
  const page = Number.isFinite(spec.page) ? Math.max(1, Math.floor(spec.page)) : 1
  const pageSize = Number.isFinite(spec.pageSize) ? Math.max(1, Math.floor(spec.pageSize)) : 20
  return { page, pageSize }
}
