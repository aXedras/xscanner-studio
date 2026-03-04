import type {
  ExtractOrderFromUploadInput,
  OrderExtractResponse,
  OrderItemCreateInput,
  OrderItemRow,
  OrderItemUpdateInput,
  OrderListQuery,
  OrderRow,
  OrderStatusCounts,
  OrderUpdateInput,
} from './types'

export type StoragePreview = {
  src: string
  revoke?: () => void
}

export interface IOrderService {
  extractFromUpload(input: ExtractOrderFromUploadInput): Promise<OrderExtractResponse>
  extractFromUploadDebug(input: ExtractOrderFromUploadInput): Promise<OrderExtractResponse>

  /**
   * Attribute a persisted order snapshot (and its items) to the given actor.
   *
   * This performs an in-place `updated_by` fill (only when missing) and does not
   * create a new version row.
   */
  attributePersistedSnapshot(orderId: string, actorId: string): Promise<void>

  listActivePaged(query: OrderListQuery): Promise<{ items: OrderRow[]; total: number; page: number; pageSize: number }>
  getActiveStatusCounts(input: {
    search?: string
    createdAtFrom?: string
    createdAtTo?: string
  }): Promise<OrderStatusCounts>

  findActiveByOriginalId(originalId: string): Promise<OrderRow | null>
  findHistoryByOriginalId(originalId: string): Promise<OrderRow[]>

  updateOrder(orderId: string, patch: OrderUpdateInput): Promise<OrderRow>

  resolveOriginalIdByOrderId(orderId: string): Promise<string | null>

  listActiveItems(orderId: string): Promise<OrderItemRow[]>
  listActiveItemsByOriginalId(originalId: string): Promise<OrderItemRow[]>
  findItemHistoryByOriginalId(originalId: string): Promise<OrderItemRow[]>
  createItem(input: OrderItemCreateInput): Promise<OrderItemRow>
  updateItem(itemId: string, patch: OrderItemUpdateInput): Promise<OrderItemRow>
  deleteItem(itemId: string): Promise<void>

  getPdfPreviewSrc(storagePath: string): Promise<StoragePreview | null>
}
