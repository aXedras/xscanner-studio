import type { ILogger } from '../../../../lib/utils/logging'
import type { IStorageService } from '../../storage/IStorageService'
import type { IXScannerClient } from '../../xscanner/IXScannerClient'
import type { IOrderRepository } from '../repository/IOrderRepository'
import type { IOrderItemRepository } from '../repository/IOrderItemRepository'
import type { IOrderService } from '../IOrderService'
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
} from '../types'

export class OrderService implements IOrderService {
  private readonly repo: IOrderRepository
  private readonly itemRepo: IOrderItemRepository
  private readonly xscanner: IXScannerClient
  private readonly storage: IStorageService
  private readonly logger: ILogger

  constructor(
    repo: IOrderRepository,
    itemRepo: IOrderItemRepository,
    xscanner: IXScannerClient,
    storage: IStorageService,
    logger: ILogger
  ) {
    this.repo = repo
    this.itemRepo = itemRepo
    this.xscanner = xscanner
    this.storage = storage
    this.logger = logger
  }

  async extractFromUpload(input: ExtractOrderFromUploadInput): Promise<OrderExtractResponse> {
    try {
      return await this.xscanner.extractOrderFromUpload(input)
    } catch (error) {
      this.logger.error('OrderService', 'extractFromUpload failed', error)
      throw error
    }
  }

  async attributePersistedSnapshot(orderId: string, actorId: string): Promise<void> {
    const id = String(orderId ?? '').trim()
    const actor = String(actorId ?? '').trim()
    if (!id || !actor) return

    try {
      await Promise.all([this.repo.setSnapshotUpdatedBy(id, actor), this.itemRepo.setSnapshotItemsUpdatedBy(id, actor)])
    } catch (error) {
      this.logger.error('OrderService', 'attributePersistedSnapshot failed', error)
      throw error
    }
  }

  async extractFromUploadDebug(input: ExtractOrderFromUploadInput): Promise<OrderExtractResponse> {
    try {
      return await this.xscanner.extractOrderFromUploadDebug(input)
    } catch (error) {
      this.logger.error('OrderService', 'extractFromUploadDebug failed', error)
      throw error
    }
  }

  async listActivePaged(
    query: OrderListQuery
  ): Promise<{ items: OrderRow[]; total: number; page: number; pageSize: number }> {
    return await this.repo.findActivePaged(query)
  }

  async getActiveStatusCounts(input: {
    search?: string
    createdAtFrom?: string
    createdAtTo?: string
  }): Promise<OrderStatusCounts> {
    return await this.repo.getActiveStatusCounts(input)
  }

  async findActiveByOriginalId(originalId: string): Promise<OrderRow | null> {
    return await this.repo.findActiveByOriginalId(originalId)
  }

  async findHistoryByOriginalId(originalId: string): Promise<OrderRow[]> {
    return await this.repo.findHistoryByOriginalId(originalId)
  }

  async updateOrder(orderId: string, patch: OrderUpdateInput): Promise<OrderRow> {
    return await this.repo.update(orderId, patch)
  }

  async resolveOriginalIdByOrderId(orderId: string): Promise<string | null> {
    const row = await this.repo.findById(orderId)
    return row?.original_id ?? null
  }

  async listActiveItems(orderId: string): Promise<OrderItemRow[]> {
    return await this.itemRepo.findActiveByOrderId(orderId)
  }

  async listActiveItemsByOriginalId(originalId: string): Promise<OrderItemRow[]> {
    const [activeOrder, versions] = await Promise.all([
      this.repo.findActiveByOriginalId(originalId),
      this.repo.findHistoryByOriginalId(originalId),
    ])

    const orderIds = versions.map(v => v.id)
    const activeOrderId = activeOrder?.id ?? null

    // Fetch active items across all order versions.
    const allActiveItems = await this.itemRepo.findActiveByOrderIds(orderIds)
    if (allActiveItems.length === 0) return []

    // Prefer items that belong to the active order version.
    if (activeOrderId) {
      const activeVersionItems = allActiveItems.filter(it => it.order_id === activeOrderId)
      if (activeVersionItems.length > 0) return activeVersionItems
    }

    // Fallback: pick the newest order version that has active items.
    // `versions` is ordered by created_at DESC (repo). We select the first with items.
    const byOrderId = new Map<string, OrderItemRow[]>()
    for (const row of allActiveItems) {
      const key = row.order_id
      const existing = byOrderId.get(key)
      if (existing) existing.push(row)
      else byOrderId.set(key, [row])
    }

    for (const v of versions) {
      const rows = byOrderId.get(v.id)
      if (rows && rows.length > 0) return rows
    }

    return []
  }

  async findItemHistoryByOriginalId(originalId: string): Promise<OrderItemRow[]> {
    return await this.itemRepo.findHistoryByOriginalId(originalId)
  }

  async createItem(input: OrderItemCreateInput): Promise<OrderItemRow> {
    return await this.itemRepo.create(input)
  }

  async updateItem(itemId: string, patch: OrderItemUpdateInput): Promise<OrderItemRow> {
    return await this.itemRepo.update(itemId, patch)
  }

  async deleteItem(itemId: string): Promise<void> {
    return await this.itemRepo.delete(itemId)
  }

  async getPdfPreviewSrc(storagePath: string) {
    return await this.storage.getFilePreviewSrc(storagePath)
  }
}
