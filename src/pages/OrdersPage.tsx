import { useCallback, useMemo, useState } from 'react'
import { useLocation, useOutletContext } from 'react-router-dom'
import { useAppTranslation, I18N_SCOPES } from '../lib/i18n'
import { PageHeader } from '../components/layout/PageHeader'
import { services } from '../services'
import type { OrderListQuery, OrderRow, OrderStatus } from '../services/core/order/types'
import { useUiMessages } from '../ui/messages/UiMessagesContext'
import { createErrorMessage } from '../ui/messages/fromError'
import { OrderStatusCards } from './orders/OrderStatusCards'
import { OrdersTable } from './orders/OrdersTable'
import { isAllowedOrderStatusFilter, useOrdersPageState } from './orders/useOrdersPageState'
import { useLoadPagedRows, useLoadStatusCounts, useStatusFilterFromUrl } from './shared/useListPageData'
import type { AuthSessionUser } from '../services/core/auth/types'

export default function OrdersPage() {
  const { t, i18n } = useAppTranslation(I18N_SCOPES.order)
  const { push } = useUiMessages()
  const location = useLocation()
  useOutletContext<{ user: AuthSessionUser }>()

  const { state, actions, derived } = useOrdersPageState()

  const [loading, setLoading] = useState(true)
  const [rows, setRows] = useState<OrderRow[]>([])
  const [total, setTotal] = useState(0)
  const [counts, setCounts] = useState<{
    pending: number
    validated: number
    corrected: number
    rejected: number
    error: number
    closed: number
  } | null>(null)
  const [countsBusy, setCountsBusy] = useState(false)

  useStatusFilterFromUrl({
    search: location.search,
    isAllowed: isAllowedOrderStatusFilter,
    setStatusFilters: actions.setStatusFilters,
  })

  const query: OrderListQuery = useMemo(
    () => ({
      page: state.page,
      pageSize: state.pageSize,
      sort: state.sort,
      search: state.search,
      statuses: state.statusFilters.length > 0 ? state.statusFilters : undefined,
    }),
    [state.page, state.pageSize, state.search, state.sort, state.statusFilters]
  )

  const countsFilters = useMemo(() => ({ search: state.search }), [state.search])

  const onError = useCallback(
    (error: unknown) => {
      push(createErrorMessage(t, error))
    },
    [push, t]
  )

  const loadPagedOrders = useCallback((nextQuery: OrderListQuery) => {
    return services.orderService.listActivePaged(nextQuery)
  }, [])

  const loadOrderStatusCounts = useCallback((filters: { search?: string }) => {
    return services.orderService.getActiveStatusCounts(filters)
  }, [])

  useLoadPagedRows({
    query,
    refreshKey: state.refreshKey,
    load: loadPagedOrders,
    onError,
    setLoading,
    setRows,
    setTotal,
  })

  useLoadStatusCounts({
    filters: countsFilters,
    refreshKey: state.refreshKey,
    load: loadOrderStatusCounts,
    onError,
    setBusy: setCountsBusy,
    setCounts,
  })

  const onToggleStatusCard = useCallback(
    (status: OrderStatus) => {
      actions.toggleStatusFilter(status)
    },
    [actions]
  )

  const clearAllFilters = useCallback(() => {
    actions.clearFilters()
  }, [actions])

  return (
    <div>
      <PageHeader
        title={t('order.list.title')}
        subtitle={t('order.list.subtitle')}
        backLabel={t('common.action.back')}
      />

      <OrderStatusCards
        counts={counts}
        busy={countsBusy}
        activeFilters={state.statusFilters}
        onToggle={onToggleStatusCard}
        labels={{
          pending: t('order.list.stats.pending'),
          validated: t('order.list.stats.validated'),
          corrected: t('order.list.stats.corrected'),
          rejected: t('order.list.stats.rejected'),
          error: t('order.list.stats.errors'),
          closed: t('order.list.stats.closed'),
        }}
      />

      <div id="orders-table" className="panel">
        <OrdersTable
          rows={rows}
          total={total}
          loading={loading}
          t={t}
          language={i18n.language}
          sort={state.sort}
          onSortChange={actions.setSort}
          searchInput={state.searchInput}
          onSearchInputChange={actions.setSearchInput}
          hasAnyFilter={derived.hasAnyFilter}
          onClearFilters={clearAllFilters}
          page={state.page}
          pageSize={state.pageSize}
          onPageChange={actions.setPage}
          onPageSizeChange={next => actions.setPageSize(next)}
        />
      </div>
    </div>
  )
}
