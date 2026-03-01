import { useEffect } from 'react'

type BaseListPageState = {
  statusFilters: unknown[]
  page: number
  pageSize: number
  sort: unknown
  searchInput: string
  search: string
  refreshKey: number
}

export function mergeBaseListPageState<TState extends BaseListPageState>(
  initialState: TState,
  override?: Partial<TState>
): TState {
  if (!override) return initialState

  return {
    ...initialState,
    ...override,
    statusFilters: Array.isArray(override.statusFilters) ? override.statusFilters : initialState.statusFilters,
    sort: override.sort ?? initialState.sort,
    page: typeof override.page === 'number' ? override.page : initialState.page,
    pageSize: typeof override.pageSize === 'number' ? override.pageSize : initialState.pageSize,
    searchInput: typeof override.searchInput === 'string' ? override.searchInput : initialState.searchInput,
    search: typeof override.search === 'string' ? override.search : initialState.search,
    refreshKey: typeof override.refreshKey === 'number' ? override.refreshKey : initialState.refreshKey,
  }
}

export function toggleFilterValue<TValue extends string>(values: TValue[], value: TValue): TValue[] {
  return values.includes(value) ? values.filter(entry => entry !== value) : [...values, value]
}

export function useDebouncedSearchSync(params: {
  searchInput: string
  search: string
  onApply: (value: string) => void
  delayMs?: number
}) {
  const { searchInput, search, onApply, delayMs = 250 } = params

  useEffect(() => {
    if (searchInput === search) return
    const handle = setTimeout(() => {
      onApply(searchInput)
    }, delayMs)
    return () => clearTimeout(handle)
  }, [delayMs, onApply, search, searchInput])
}
