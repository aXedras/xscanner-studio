import type { SortSpec } from '../../services/shared/persistence/query'
import { DataTablePaginationControls } from './DataTablePaginationControls'
import type { DataTableProps } from './DataTableTypes'

export type { DataTableColumn, DataTablePagination, DataTablePaginationPlacement } from './DataTableTypes'

function toggleSort<SortField extends string>(
  current: SortSpec<SortField> | undefined,
  field: SortField
): SortSpec<SortField> {
  if (!current || current.field !== field) {
    return { field, direction: 'desc' }
  }

  return { field, direction: current.direction === 'desc' ? 'asc' : 'desc' }
}

function sortIndicator(direction: 'asc' | 'desc'): string {
  return direction === 'asc' ? '▲' : '▼'
}

export function DataTable<Row, SortField extends string>({
  columns,
  rows,
  rowKey,
  loading = false,
  loadingLabel,
  keepRowsOnLoading = false,
  empty,
  toolbar,
  toolbarBelow,
  sort,
  onSortChange,
  pagination,
  paginationPlacement = 'bottom',
}: DataTableProps<Row, SortField>) {
  const showEmpty = !loading && rows.length === 0
  const showOverlayLoading = Boolean(loading && keepRowsOnLoading && rows.length > 0)

  const totalPages = pagination ? Math.max(1, Math.ceil(pagination.total / pagination.pageSize)) : 1

  const paginationControls = pagination ? (
    <DataTablePaginationControls pagination={pagination} totalPages={totalPages} />
  ) : null

  const showTopBar = Boolean(toolbar || toolbarBelow || (pagination && paginationPlacement === 'top'))

  return (
    <div>
      {showTopBar ? (
        <div className="mb-3 flex flex-col gap-2">
          <div className="flex flex-nowrap items-center justify-between gap-3">
            <div className="min-w-0 flex-1">{toolbar}</div>
            {paginationPlacement === 'top' ? <div className="flex-none">{paginationControls}</div> : null}
          </div>
          {toolbarBelow ? <div className="w-full">{toolbarBelow}</div> : null}
        </div>
      ) : null}

      <div className="relative overflow-x-auto">
        {showOverlayLoading ? (
          <div className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center">
            <div className="rounded-md border border-[color:var(--bg-card-border)] bg-white/75 px-3 py-2 text-sm shadow-sm dark:bg-black/40">
              {loadingLabel ?? <div className="text-label">…</div>}
            </div>
          </div>
        ) : null}

        <table className="min-w-full text-sm">
          <thead className="text-left">
            <tr className="table-divider-strong">
              {columns.map(col => {
                const isSortable = Boolean(col.sortField && onSortChange)
                const isActive = Boolean(sort && col.sortField && sort.field === col.sortField)

                return (
                  <th key={col.key} className={`py-3 pr-4 ${col.headerClassName ?? ''}`.trim()}>
                    {isSortable && col.sortField ? (
                      <button
                        type="button"
                        className="inline-flex items-center gap-2 text-left hover:underline"
                        onClick={() => onSortChange?.(toggleSort(sort, col.sortField!))}
                      >
                        <span>{col.header}</span>
                        {isActive ? <span className="text-xs">{sortIndicator(sort!.direction)}</span> : null}
                      </button>
                    ) : (
                      col.header
                    )}
                  </th>
                )
              })}
            </tr>
          </thead>
          <tbody>
            {loading && !showOverlayLoading ? (
              <tr>
                <td className="py-6" colSpan={columns.length}>
                  {loadingLabel ?? <div className="text-label">…</div>}
                </td>
              </tr>
            ) : showEmpty ? (
              <tr>
                <td className="py-6" colSpan={columns.length}>
                  {empty ?? <div className="text-label">—</div>}
                </td>
              </tr>
            ) : (
              rows.map(row => (
                <tr key={rowKey(row)} className="table-divider">
                  {columns.map(col => (
                    <td key={col.key} className={`py-3 pr-4 ${col.cellClassName ?? ''}`.trim()}>
                      {col.cell(row)}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {pagination && paginationPlacement === 'bottom' ? <div className="mt-3">{paginationControls}</div> : null}
    </div>
  )
}
