import type { PageSpec, SortSpec } from '../../../shared/query/types'

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

export type OrderStatus = 'pending' | 'validated' | 'corrected' | 'rejected' | 'error' | 'closed'

export type OrderDocumentType = 'invoice' | 'order_confirmation' | 'delivery_note' | 'unknown'

export type BullionMetal = 'gold' | 'silver' | 'platinum' | 'palladium' | 'unknown'
export type BullionWeightUnit = 'g' | 'kg' | 'oz' | 'lb' | 'unknown'
export type BullionForm = 'bar' | 'coin' | 'round' | 'unknown'

export const ORDER_ENUMS = {
  bullion_metal: ['gold', 'silver', 'platinum', 'palladium', 'unknown'] as const,
  bullion_weight_unit: ['g', 'kg', 'oz', 'lb', 'unknown'] as const,
  bullion_form: ['bar', 'coin', 'round', 'unknown'] as const,
} as const

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

export type OrderRow = {
  id: string
  original_id: string
  updated_by: string | null
  storage_path: string
  pdf_filename: string | null
  document_issuer: string
  document_type: OrderDocumentType
  document_number: string
  document_date: string
  order_number: string | null
  order_date: string | null
  value_date: string | null
  shipping_date: string | null
  transaction_type: string | null
  seller_name: string | null
  buyer_name: string | null
  currency: string | null
  shipping_charges_amount: number | null
  other_charges_amount: number | null
  subtotal_amount: number | null
  total_amount: number | null
  strategy_used: string
  confidence: number | null
  processing_time: number | null
  extracted_data: Record<string, unknown>
  status: OrderStatus
  error: string | null
  is_active: boolean
  created_at: string
}

export type OrderCreateInput = Partial<OrderRow> & {
  original_id: string
  storage_path: string
  document_issuer: string
  document_type: OrderDocumentType
  document_number: string
  document_date: string
}

export type OrderUpdateInput = Partial<OrderRow>

export type OrderItemRow = {
  id: string
  order_id: string
  original_id: string
  updated_by: string | null
  serial_number: string | null
  item: string | null
  description: string | null
  quantity: string | null
  item_price: number | null
  total_price: number | null
  metal: BullionMetal
  weight: string | null
  weight_unit: BullionWeightUnit
  fineness: string | null
  producer: string | null
  form: BullionForm
  raw: Record<string, unknown>
  is_active: boolean
  created_at: string
}

export type OrderItemCreateInput = Partial<OrderItemRow> & {
  order_id: string
  original_id: string
}

export type OrderItemUpdateInput = Partial<OrderItemRow>

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
