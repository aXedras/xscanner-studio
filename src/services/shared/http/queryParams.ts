type SortInput = {
  field?: string
  direction?: string
}

type DateFilterInput = {
  search?: string
  createdAtFrom?: string
  createdAtTo?: string
}

export type PagedListQueryInput = DateFilterInput & {
  page: number
  pageSize: number
  sort?: SortInput
  statuses?: string[]
}

function addTrimmedParam(params: URLSearchParams, key: string, value: string | undefined): void {
  const trimmed = (value ?? '').trim()
  if (trimmed) params.set(key, trimmed)
}

export function withQuery(path: string, query: string): string {
  if (!query) return path
  return `${path}?${query}`
}

export function buildPagedListQuery(query: PagedListQueryInput): string {
  const params = new URLSearchParams()

  params.set('page', String(query.page))
  params.set('page_size', String(query.pageSize))

  if (query.sort?.field) params.set('sort_field', query.sort.field)
  if (query.sort?.direction) params.set('sort_direction', query.sort.direction)

  addTrimmedParam(params, 'search', query.search)
  addTrimmedParam(params, 'created_at_from', query.createdAtFrom)
  addTrimmedParam(params, 'created_at_to', query.createdAtTo)

  for (const status of query.statuses ?? []) {
    params.append('status', status)
  }

  return params.toString()
}

export function buildStatusCountQuery(input: DateFilterInput): string {
  const params = new URLSearchParams()

  addTrimmedParam(params, 'search', input.search)
  addTrimmedParam(params, 'created_at_from', input.createdAtFrom)
  addTrimmedParam(params, 'created_at_to', input.createdAtTo)

  return params.toString()
}
