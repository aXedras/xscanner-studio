import type { IRepository } from '../../../shared/persistence/IRepository'
import type { OrderCreateInput, OrderListQuery, OrderRow, OrderStatusCounts, OrderUpdateInput } from '../types'

export interface IOrderRepository extends IRepository<OrderRow, OrderCreateInput, OrderUpdateInput> {
  findActivePaged(query: OrderListQuery): Promise<{ items: OrderRow[]; total: number; page: number; pageSize: number }>

  getActiveStatusCounts(input: {
    search?: string
    createdAtFrom?: string
    createdAtTo?: string
  }): Promise<OrderStatusCounts>

  findById(id: string): Promise<OrderRow | null>
  findActiveByOriginalId(originalId: string): Promise<OrderRow | null>
  findHistoryByOriginalId(originalId: string): Promise<OrderRow[]>

  /**
   * Set `updated_by` on an existing snapshot row without creating a new version.
   *
   * This is used to attribute server-persisted snapshots to the initiating user
   * when the API call itself is intentionally unauthenticated.
   */
  setSnapshotUpdatedBy(orderId: string, updatedBy: string): Promise<void>
}
