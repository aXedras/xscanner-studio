import { useMemo, useReducer } from 'react'
import type { OrderListSortField, OrderStatus } from '../../services/core/order/types'
import type { SortSpec } from '../../services/shared/query/types'
import { mergeBaseListPageState, toggleFilterValue, useDebouncedSearchSync } from '../shared/listPageState'

export type OrdersPageState = {
  statusFilters: OrderStatus[]
  page: number
  pageSize: number
  sort: SortSpec<OrderListSortField>
  searchInput: string
  search: string
  refreshKey: number
}

type Action =
  | { type: 'SET_STATUS_FILTERS'; value: OrderStatus[] }
  | { type: 'TOGGLE_STATUS_FILTER'; value: OrderStatus }
  | { type: 'SET_PAGE'; value: number }
  | { type: 'SET_PAGE_SIZE'; value: number }
  | { type: 'SET_SORT'; value: SortSpec<OrderListSortField> }
  | { type: 'SET_SEARCH_INPUT'; value: string }
  | { type: 'SET_SEARCH'; value: string }
  | { type: 'CLEAR_FILTERS' }

const initialState: OrdersPageState = {
  statusFilters: [],
  page: 1,
  pageSize: 10,
  sort: { field: 'created_at', direction: 'desc' },
  searchInput: '',
  search: '',
  refreshKey: 0,
}

function mergeInitialState(override?: Partial<OrdersPageState>): OrdersPageState {
  return mergeBaseListPageState(initialState, override)
}

function reducer(state: OrdersPageState, action: Action): OrdersPageState {
  switch (action.type) {
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
      return { ...state, searchInput: '', search: '', statusFilters: [], page: 1, refreshKey: state.refreshKey + 1 }
    default:
      return state
  }
}

export function useOrdersPageState(initial?: Partial<OrdersPageState>) {
  const [state, dispatch] = useReducer(reducer, initial, mergeInitialState)

  useDebouncedSearchSync({
    searchInput: state.searchInput,
    search: state.search,
    onApply: value => dispatch({ type: 'SET_SEARCH', value }),
  })

  const actions = useMemo(
    () => ({
      setStatusFilters: (value: OrderStatus[]) => dispatch({ type: 'SET_STATUS_FILTERS', value }),
      toggleStatusFilter: (value: OrderStatus) => dispatch({ type: 'TOGGLE_STATUS_FILTER', value }),
      setPage: (value: number) => dispatch({ type: 'SET_PAGE', value }),
      setPageSize: (value: number) => dispatch({ type: 'SET_PAGE_SIZE', value }),
      setSort: (value: SortSpec<OrderListSortField>) => dispatch({ type: 'SET_SORT', value }),
      setSearchInput: (value: string) => dispatch({ type: 'SET_SEARCH_INPUT', value }),
      clearFilters: () => dispatch({ type: 'CLEAR_FILTERS' }),
    }),
    []
  )

  const derived = useMemo(
    () => ({
      hasAnyFilter: Boolean(state.searchInput.trim()) || state.statusFilters.length > 0,
    }),
    [state.searchInput, state.statusFilters.length]
  )

  return { state, actions, derived }
}

export function isAllowedOrderStatusFilter(value: string | null): value is OrderStatus {
  if (!value) return false
  return (
    value === 'pending' ||
    value === 'validated' ||
    value === 'corrected' ||
    value === 'rejected' ||
    value === 'error' ||
    value === 'closed'
  )
}
