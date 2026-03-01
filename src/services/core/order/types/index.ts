import type { Tables, TablesInsert, TablesUpdate } from '../../../../lib/supabase/database.types'
import type { PageSpec, SortSpec } from '../../../shared/persistence/query'

export type OrderStrategyChoice = 'manual' | 'cloud' | 'local' | 'auto'

export type ExtractOrderFromUploadInput = {
  files: File[]
  strategy: OrderStrategyChoice
  useMock: boolean
}

export type OrderExtractionMeta = {
  // Kept intentionally flexible; server-owned.
  [key: string]: unknown
}

export type OrderExtractionRaw = {
  raw_kv: Record<string, unknown>
  raw_tables: unknown[]
  raw_text?: string | null
  marker_text?: string | null
  pdf_text?: string | null
}

export type OrderExtractionResult = {
  structured_data: Record<string, unknown>
  meta: OrderExtractionMeta
  raw: OrderExtractionRaw | null
}

export type OrderExtractResponse = {
  success: boolean
  request_id: string
  order_id: string | null
  result: OrderExtractionResult | Record<string, unknown>
  processing_time: number | null
  strategy_used: string | null
  error: string | null
}

export type OrderStatus = Tables<'order'>['status']

export type OrderDocumentType = Tables<'order'>['document_type']

export function getOrderStatusLabelKey(status: OrderStatus): string {
  switch (status) {
    case 'pending':
      return 'order.list.stats.pending'
    case 'validated':
      return 'order.list.stats.validated'
    case 'corrected':
      return 'order.list.stats.corrected'
    case 'rejected':
      return 'order.list.stats.rejected'
    case 'closed':
      return 'order.list.stats.closed'
    case 'error':
      return 'common.status.error'
    default: {
      const _exhaustiveCheck: never = status
      return _exhaustiveCheck
    }
  }
}

export function getOrderDocumentTypeLabelKey(documentType: OrderDocumentType): string {
  switch (documentType) {
    case 'invoice':
      return 'order.documentType.invoice'
    case 'order_confirmation':
      return 'order.documentType.orderConfirmation'
    case 'delivery_note':
      return 'order.documentType.deliveryNote'
    case 'unknown':
      return 'order.documentType.unknown'
    default: {
      const _exhaustiveCheck: never = documentType
      return _exhaustiveCheck
    }
  }
}

export type OrderRow = Tables<'order'>
export type OrderCreateInput = TablesInsert<'order'>
export type OrderUpdateInput = TablesUpdate<'order'>

export type OrderItemRow = Tables<'order_item'>
export type OrderItemCreateInput = TablesInsert<'order_item'>
export type OrderItemUpdateInput = TablesUpdate<'order_item'>

export type OrderListSortField =
  | 'created_at'
  | 'status'
  | 'document_issuer'
  | 'document_number'
  | 'document_date'
  | 'order_number'
  | 'total_amount'

export type OrderListQuery = PageSpec & {
  sort?: SortSpec<OrderListSortField>
  search?: string
  createdAtFrom?: string
  createdAtTo?: string
  statuses?: OrderStatus[]
}

export type OrderStatusCounts = {
  pending: number
  validated: number
  corrected: number
  rejected: number
  error: number
  closed: number
}
