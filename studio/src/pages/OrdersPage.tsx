import { useCallback, useEffect, useMemo, useState } from 'react'
import { useLocation, useOutletContext } from 'react-router-dom'
import type { User } from '@supabase/supabase-js'
import { useAppTranslation, I18N_SCOPES } from '../lib/i18n'
import { PageHeader } from '../components/layout/PageHeader'
import { services } from '../services'
import type { OrderListQuery, OrderRow, OrderStatus } from '../services/core/order/types'
import { useUiMessages } from '../ui/messages/UiMessagesContext'
import { createErrorMessage } from '../ui/messages/fromError'
import { OrderStatusCards } from './orders/OrderStatusCards'
import { OrdersTable } from './orders/OrdersTable'
import { isAllowedOrderStatusFilter, useOrdersPageState } from './orders/useOrdersPageState'

export default function OrdersPage() {
  const { t, i18n } = useAppTranslation(I18N_SCOPES.order)
  const { push } = useUiMessages()
  const location = useLocation()
  useOutletContext<{ user: User }>()

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

  useEffect(() => {
    const params = new URLSearchParams(location.search)
    const status = params.get('status')?.trim() ?? null
    if (isAllowedOrderStatusFilter(status)) actions.setStatusFilters([status])
  }, [actions, location.search])

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

  useEffect(() => {
    let isMounted = true

    const run = async () => {
      setLoading(true)
      try {
        const result = await services.orderService.listActivePaged(query)
        if (!isMounted) return
        setRows(result.items)
        setTotal(result.total)
      } catch (error) {
        push(createErrorMessage(t, error))
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    run()
    return () => {
      isMounted = false
    }
  }, [push, query, state.refreshKey, t])

  useEffect(() => {
    let isMounted = true

    const run = async () => {
      setCountsBusy(true)
      try {
        const nextCounts = await services.orderService.getActiveStatusCounts(countsFilters)
        if (!isMounted) return
        setCounts(nextCounts)
      } catch (error) {
        push(createErrorMessage(t, error))
      } finally {
        if (isMounted) setCountsBusy(false)
      }
    }

    run()
    return () => {
      isMounted = false
    }
  }, [countsFilters, push, state.refreshKey, t])

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
