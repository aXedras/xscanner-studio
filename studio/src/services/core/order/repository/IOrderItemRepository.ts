import type { IRepository } from '../../../shared/persistence/IRepository'
import type { OrderItemCreateInput, OrderItemRow, OrderItemUpdateInput } from '../types'

export interface IOrderItemRepository extends IRepository<OrderItemRow, OrderItemCreateInput, OrderItemUpdateInput> {
  findActiveByOrderId(orderId: string): Promise<OrderItemRow[]>
  findActiveByOrderIds(orderIds: string[]): Promise<OrderItemRow[]>
  findHistoryByOriginalId(originalId: string): Promise<OrderItemRow[]>

  /**
   * Set `updated_by` for all item snapshots that belong to a given order snapshot.
   * Updates rows in-place and only fills missing `updated_by`.
   */
  setSnapshotItemsUpdatedBy(orderId: string, updatedBy: string): Promise<void>
}
