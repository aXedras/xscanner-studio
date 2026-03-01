import { useMemo, useReducer } from 'react'
import type { ExtractionListSortField, ExtractionStatus } from '../../services/core/extraction/types'
import type { SortSpec } from '../../services/shared/persistence/query'
import { mergeBaseListPageState, toggleFilterValue, useDebouncedSearchSync } from '../shared/listPageState'

export type ExtractionsPageState = {
  showFilters: boolean
  createdAtFrom: string
  createdAtTo: string
  statusFilters: ExtractionStatus[]
  page: number
  pageSize: number
  sort: SortSpec<ExtractionListSortField>
  searchInput: string
  search: string
  refreshKey: number
}

type Action =
  | { type: 'TOGGLE_FILTERS' }
  | { type: 'SET_SHOW_FILTERS'; value: boolean }
  | { type: 'SET_DATE_RANGE'; from: string; to: string }
  | { type: 'SET_STATUS_FILTERS'; value: ExtractionStatus[] }
  | { type: 'TOGGLE_STATUS_FILTER'; value: ExtractionStatus }
  | { type: 'SET_PAGE'; value: number }
  | { type: 'SET_PAGE_SIZE'; value: number }
  | { type: 'SET_SORT'; value: SortSpec<ExtractionListSortField> }
  | { type: 'SET_SEARCH_INPUT'; value: string }
  | { type: 'SET_SEARCH'; value: string }
  | { type: 'CLEAR_FILTERS' }

const initialState: ExtractionsPageState = {
  showFilters: false,
  createdAtFrom: '',
  createdAtTo: '',
  statusFilters: [],
  page: 1,
  pageSize: 10,
  sort: { field: 'created_at', direction: 'desc' },
  searchInput: '',
  search: '',
  refreshKey: 0,
}

function mergeInitialState(override?: Partial<ExtractionsPageState>): ExtractionsPageState {
  const mergedBase = mergeBaseListPageState(initialState, override)
  if (!override) return mergedBase

  return {
    ...mergedBase,
    showFilters: typeof override.showFilters === 'boolean' ? override.showFilters : initialState.showFilters,
    createdAtFrom: typeof override.createdAtFrom === 'string' ? override.createdAtFrom : initialState.createdAtFrom,
    createdAtTo: typeof override.createdAtTo === 'string' ? override.createdAtTo : initialState.createdAtTo,
  }
}

function reducer(state: ExtractionsPageState, action: Action): ExtractionsPageState {
  switch (action.type) {
    case 'TOGGLE_FILTERS':
      return { ...state, showFilters: !state.showFilters }
    case 'SET_SHOW_FILTERS':
      return { ...state, showFilters: action.value }
    case 'SET_DATE_RANGE':
      return { ...state, createdAtFrom: action.from, createdAtTo: action.to, page: 1 }
    case 'SET_STATUS_FILTERS':
      return { ...state, statusFilters: action.value, page: 1 }
    case 'TOGGLE_STATUS_FILTER': {
      const next = toggleFilterValue(state.statusFilters, action.value)
      return { ...state, statusFilters: next, page: 1 }
    }
    case 'SET_PAGE':
      return { ...state, page: action.value }
    case 'SET_PAGE_SIZE':
      return { ...state, pageSize: action.value, page: 1 }
    case 'SET_SORT':
      return { ...state, sort: action.value }
    case 'SET_SEARCH_INPUT':
      return { ...state, searchInput: action.value }
    case 'SET_SEARCH':
      return { ...state, search: action.value, page: 1 }
    case 'CLEAR_FILTERS':
      return {
        ...state,
        showFilters: false,
        searchInput: '',
        search: '',
        createdAtFrom: '',
        createdAtTo: '',
        statusFilters: [],
        page: 1,
        refreshKey: state.refreshKey + 1,
      }
    default:
      return state
  }
}

export function useExtractionsPageState(initial?: Partial<ExtractionsPageState>) {
  const [state, dispatch] = useReducer(reducer, initial, mergeInitialState)

  useDebouncedSearchSync({
    searchInput: state.searchInput,
    search: state.search,
    onApply: value => dispatch({ type: 'SET_SEARCH', value }),
  })

  const actions = useMemo(
    () => ({
      toggleFilters: () => dispatch({ type: 'TOGGLE_FILTERS' }),
      setShowFilters: (value: boolean) => dispatch({ type: 'SET_SHOW_FILTERS', value }),
      setDateRange: (from: string, to: string) => dispatch({ type: 'SET_DATE_RANGE', from, to }),
      setStatusFilters: (value: ExtractionStatus[]) => dispatch({ type: 'SET_STATUS_FILTERS', value }),
      toggleStatusFilter: (value: ExtractionStatus) => dispatch({ type: 'TOGGLE_STATUS_FILTER', value }),
      setPage: (value: number) => dispatch({ type: 'SET_PAGE', value }),
      setPageSize: (value: number) => dispatch({ type: 'SET_PAGE_SIZE', value }),
      setSort: (value: SortSpec<ExtractionListSortField>) => dispatch({ type: 'SET_SORT', value }),
      setSearchInput: (value: string) => dispatch({ type: 'SET_SEARCH_INPUT', value }),
      clearFilters: () => dispatch({ type: 'CLEAR_FILTERS' }),
    }),
    []
  )

  const derived = useMemo(
    () => ({
      hasAnyFilter:
        Boolean(state.searchInput.trim()) ||
        Boolean(state.createdAtFrom.trim()) ||
        Boolean(state.createdAtTo.trim()) ||
        state.statusFilters.length > 0,
    }),
    [state.createdAtFrom, state.createdAtTo, state.searchInput, state.statusFilters.length]
  )

  return { state, actions, derived }
}

export function isAllowedStatusFilter(value: string | null): value is ExtractionStatus {
  if (!value) return false
  return (
    value === 'pending' || value === 'corrected' || value === 'validated' || value === 'rejected' || value === 'error'
  )
}
