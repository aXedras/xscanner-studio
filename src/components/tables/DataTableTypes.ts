import type { ReactNode } from 'react'
import type { SortSpec } from '../../services/shared/query/types'

export type DataTableColumn<Row, SortField extends string> = {
  key: string
  header: ReactNode
  cell: (row: Row) => ReactNode
  sortField?: SortField
  headerClassName?: string
  cellClassName?: string
}

export type DataTablePagination = {
  page: number
  pageSize: number
  total: number
  pageSizeOptions?: number[]
  onPageChange: (page: number) => void
  onPageSizeChange: (pageSize: number) => void
  labelRowsPerPage: string
  labelPage: string
  labelPrev: string
  labelNext: string
}

export type DataTablePaginationPlacement = 'top' | 'bottom'

export type DataTableProps<Row, SortField extends string> = {
  columns: Array<DataTableColumn<Row, SortField>>
  rows: Row[]
  rowKey: (row: Row) => string
  loading?: boolean
  loadingLabel?: ReactNode
  keepRowsOnLoading?: boolean
  empty?: ReactNode
  toolbar?: ReactNode
  toolbarBelow?: ReactNode
  sort?: SortSpec<SortField>
  onSortChange?: (sort: SortSpec<SortField>) => void
  pagination?: DataTablePagination
  paginationPlacement?: DataTablePaginationPlacement
}
