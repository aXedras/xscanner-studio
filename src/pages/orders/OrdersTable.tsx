import { useMemo } from 'react'
import type { TFunction } from 'i18next'
import { DataTable } from '../../components/tables/DataTable'
import type { SortSpec } from '../../services/shared/persistence/query'
import type { OrderListSortField, OrderRow } from '../../services/core/order/types'
import { createOrdersTableColumns } from './ordersTableColumns'

type Props = {
  rows: OrderRow[]
  total: number
  loading: boolean
  t: TFunction
  language: string

  sort: SortSpec<OrderListSortField>
  onSortChange: (sort: SortSpec<OrderListSortField>) => void

  searchInput: string
  onSearchInputChange: (next: string) => void

  hasAnyFilter: boolean
  onClearFilters: () => void

  page: number
  pageSize: number
  onPageChange: (page: number) => void
  onPageSizeChange: (pageSize: number) => void
}

export function OrdersTable({
  rows,
  total,
  loading,
  t,
  language,
  sort,
  onSortChange,
  searchInput,
  onSearchInputChange,
  hasAnyFilter,
  onClearFilters,
  page,
  pageSize,
  onPageChange,
  onPageSizeChange,
}: Props) {
  const columns = useMemo(() => createOrdersTableColumns({ t, language }), [language, t])

  return (
    <DataTable
      columns={columns}
      rows={rows}
      rowKey={row => String(row.id)}
      loading={loading}
      keepRowsOnLoading
      loadingLabel={<div className="py-4">{t('common.status.loading')}</div>}
      empty={<div className="py-4">{t('order.list.empty')}</div>}
      sort={sort}
      onSortChange={onSortChange}
      toolbar={
        <div className="flex min-w-0 items-center gap-2">
          <input
            className="input min-w-0 flex-1"
            value={searchInput}
            placeholder={t('common.fields.search')}
            onChange={e => onSearchInputChange(e.target.value)}
          />

          <button type="button" className="btn btn-outline" onClick={onClearFilters} disabled={!hasAnyFilter}>
            {t('common.action.clear')}
          </button>
        </div>
      }
      pagination={{
        page,
        pageSize,
        total,
        pageSizeOptions: [10, 20, 50, 100],
        onPageChange,
        onPageSizeChange,
        labelRowsPerPage: t('common.table.rowsPerPage'),
        labelPage: t('common.table.page'),
        labelPrev: t('common.action.previous'),
        labelNext: t('common.action.next'),
      }}
      paginationPlacement="top"
    />
  )
}
