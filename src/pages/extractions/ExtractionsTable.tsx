import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import type { TFunction } from 'i18next'
import { DataTable } from '../../components/tables/DataTable'
import type { SortSpec } from '../../services/shared/query/types'
import type { ExtractionListSortField, ExtractionRow, ExtractionStatus } from '../../services/core/extraction/types'
import { ExtractionsTableFilters } from './ExtractionsTableFilters'
import { createExtractionsTableColumns } from './extractionsTableColumns'
import { BulkActionsBar } from './BulkActionsBar'

type Props = {
  rows: ExtractionRow[]
  total: number
  loading: boolean
  t: TFunction
  language: string

  sort: SortSpec<ExtractionListSortField>
  onSortChange: (sort: SortSpec<ExtractionListSortField>) => void

  searchInput: string
  onSearchInputChange: (next: string) => void

  showFilters: boolean
  onToggleFilters: () => void
  onClearFilters: () => void
  hasAnyFilter: boolean

  createdAtFrom: string
  createdAtTo: string
  onDateRangeChange: (from: string, to: string) => void

  statusFilters: ExtractionStatus[]
  onStatusFiltersChange: (next: ExtractionStatus[]) => void

  page: number
  pageSize: number
  onPageChange: (page: number) => void
  onPageSizeChange: (pageSize: number) => void

  onRegister: (originalId: string) => void
  onReject: (originalId: string) => void
  onRejectMany: (originalIds: string[]) => Promise<{ ok: string[]; failed: Array<{ id: string; error: unknown }> }>
}

function isFinalStatus(status: ExtractionStatus): boolean {
  return status === 'validated' || status === 'rejected'
}

export function ExtractionsTable({
  rows,
  total,
  loading,
  t,
  language,
  sort,
  onSortChange,
  searchInput,
  onSearchInputChange,
  showFilters,
  onToggleFilters,
  onClearFilters,
  hasAnyFilter,
  createdAtFrom,
  createdAtTo,
  onDateRangeChange,
  statusFilters,
  onStatusFiltersChange,
  page,
  pageSize,
  onPageChange,
  onPageSizeChange,
  onRegister,
  onReject,
  onRejectMany,
}: Props) {
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [busyIds, setBusyIds] = useState<Set<string>>(new Set())
  const [bulkBusy, setBulkBusy] = useState(false)

  const rejectableIds = useMemo(() => {
    return rows.filter(r => !isFinalStatus(r.status)).map(r => String(r.original_id))
  }, [rows])

  const rejectableIdSet = useMemo(() => new Set(rejectableIds), [rejectableIds])

  const selectableIdsOnPage = useMemo(() => {
    return rows.map(r => String(r.original_id)).filter(id => !busyIds.has(id))
  }, [busyIds, rows])

  const selectedIds = useMemo(() => Array.from(selected), [selected])

  const eligibleRejectCount = useMemo(() => {
    if (selected.size === 0) return 0
    let count = 0
    for (const id of selected) {
      if (busyIds.has(id)) continue
      if (!rejectableIdSet.has(id)) continue
      count += 1
    }
    return count
  }, [busyIds, rejectableIdSet, selected])

  const allSelectedOnPage = selectableIdsOnPage.length > 0 && selectableIdsOnPage.every(id => selected.has(id))
  const someSelectedOnPage = selectableIdsOnPage.some(id => selected.has(id))

  const headerCheckboxRef = useRef<HTMLInputElement>(null)
  useEffect(() => {
    if (!headerCheckboxRef.current) return
    headerCheckboxRef.current.indeterminate = !allSelectedOnPage && someSelectedOnPage
  }, [allSelectedOnPage, someSelectedOnPage])

  const onToggleAllOnPage = useCallback(() => {
    setSelected(prev => {
      const next = new Set(prev)
      if (allSelectedOnPage) {
        for (const id of selectableIdsOnPage) next.delete(id)
        return next
      }
      for (const id of selectableIdsOnPage) next.add(id)
      return next
    })
  }, [allSelectedOnPage, selectableIdsOnPage])

  const onToggleRow = (id: string) => {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const clearSelection = () => setSelected(new Set())

  const bulkReject = async () => {
    if (bulkBusy) return

    const idsToReject = selectedIds.filter(id => !busyIds.has(id))

    if (idsToReject.length === 0) return

    setBulkBusy(true)
    setBusyIds(prev => new Set([...prev, ...idsToReject]))

    try {
      const result = await onRejectMany(idsToReject)

      setSelected(prev => {
        const next = new Set(prev)
        for (const id of result.ok) next.delete(id)
        return next
      })
    } finally {
      setBulkBusy(false)
      setBusyIds(prev => {
        const next = new Set(prev)
        for (const id of idsToReject) next.delete(id)
        return next
      })
    }
  }

  const columns = useMemo(
    () =>
      createExtractionsTableColumns({
        t,
        language,
        selected,
        busyIds,
        bulkBusy,
        multiSelectActive: selected.size > 0,
        selectableIdsOnPage,
        allSelectedOnPage,
        headerCheckboxRef,
        onToggleAllOnPage,
        onToggleRow,
        onRegister,
        onReject,
      }),
    [
      allSelectedOnPage,
      bulkBusy,
      busyIds,
      language,
      onToggleAllOnPage,
      onRegister,
      onReject,
      selectableIdsOnPage,
      selected,
      t,
    ]
  )

  const toolbarBelow: ReactNode = (
    <>
      <BulkActionsBar
        selectedCount={selected.size}
        eligibleCount={eligibleRejectCount}
        busy={bulkBusy}
        onReject={bulkReject}
        onClear={clearSelection}
        t={t}
      />

      <ExtractionsTableFilters
        show={showFilters}
        t={t}
        language={language}
        createdAtFrom={createdAtFrom}
        createdAtTo={createdAtTo}
        onDateRangeChange={onDateRangeChange}
        statusFilters={statusFilters}
        onStatusFiltersChange={onStatusFiltersChange}
      />
    </>
  )

  return (
    <DataTable
      columns={columns}
      rows={rows}
      rowKey={row => String(row.id)}
      loading={loading}
      keepRowsOnLoading
      loadingLabel={<div className="py-4">{t('common.status.loading')}</div>}
      empty={<div className="py-4">{t('extraction.list.empty')}</div>}
      sort={sort}
      onSortChange={onSortChange}
      toolbar={
        <div className="flex min-w-0 items-center gap-2">
          <button
            type="button"
            className={`btn btn-outline btn-icon ${showFilters ? 'ring-2 ring-[rgb(var(--color-gold-rgb)/0.40)]' : ''}`}
            aria-label={t('common.action.filters')}
            onClick={onToggleFilters}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 5h18" />
              <path d="M7 12h10" />
              <path d="M10 19h4" />
            </svg>
          </button>

          <input
            className="input min-w-0 flex-1"
            value={searchInput}
            placeholder={t('common.fields.search')}
            onChange={e => onSearchInputChange(e.target.value)}
          />

          <button
            type="button"
            className="btn btn-outline"
            onClick={onClearFilters}
            disabled={!hasAnyFilter || bulkBusy}
          >
            {t('common.action.clear')}
          </button>
        </div>
      }
      toolbarBelow={toolbarBelow}
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
