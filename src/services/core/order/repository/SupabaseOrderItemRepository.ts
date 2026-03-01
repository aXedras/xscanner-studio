import type { SupabaseClient } from '@supabase/supabase-js'
import type { ILogger } from '../../../../lib/utils/logging'
import type { OrderItemCreateInput, OrderItemRow, OrderItemUpdateInput } from '../types'
import { SupabaseCrudRepository } from '../../../infrastructure/persistence/SupabaseCrudRepository'
import type { IOrderItemRepository } from './IOrderItemRepository'

export class SupabaseOrderItemRepository
  extends SupabaseCrudRepository<OrderItemRow, OrderItemCreateInput, OrderItemUpdateInput>
  implements IOrderItemRepository
{
  constructor(supabase: SupabaseClient, logger: ILogger) {
    super(supabase, logger, { table: 'order_item' })
  }

  async findActiveByOrderId(orderId: string): Promise<OrderItemRow[]> {
    const { data, error } = await this.supabase
      .from('order_item')
      .select('*')
      .eq('order_id', orderId)
      .eq('is_active', true)
      .order('created_at', { ascending: true })

    if (error) {
      this.logger.error('SupabaseOrderItemRepository', 'findActiveByOrderId failed', error)
      throw error
    }

    return (data as OrderItemRow[]) ?? []
  }

  async findActiveByOrderIds(orderIds: string[]): Promise<OrderItemRow[]> {
    if (orderIds.length === 0) return []

    const { data, error } = await this.supabase
      .from('order_item')
      .select('*')
      .in('order_id', orderIds)
      .eq('is_active', true)
      .order('created_at', { ascending: true })

    if (error) {
      this.logger.error('SupabaseOrderItemRepository', 'findActiveByOrderIds failed', error)
      throw error
    }

    return (data as OrderItemRow[]) ?? []
  }

  async findHistoryByOriginalId(originalId: string): Promise<OrderItemRow[]> {
    const { data, error } = await this.supabase
      .from('order_item')
      .select('*')
      .or(`original_id.eq.${originalId},id.eq.${originalId}`)
      .order('created_at', { ascending: false })

    if (error) {
      this.logger.error('SupabaseOrderItemRepository', 'findHistoryByOriginalId failed', error)
      throw error
    }

    return (data as OrderItemRow[]) ?? []
  }

  override async update(itemId: string, patch: OrderItemUpdateInput): Promise<OrderItemRow> {
    // Versioned updates: create a new active row and mark the old one inactive.
    const { data: current, error: loadError } = await this.supabase
      .from('order_item')
      .select('*')
      .eq('id', itemId)
      .single()

    if (loadError) {
      this.logger.error('SupabaseOrderItemRepository', 'update (load current) failed', loadError)
      throw loadError
    }

    const currentRow = (current as OrderItemRow) ?? null
    if (!currentRow) {
      const error = new Error('Order item not found')
      this.logger.error('SupabaseOrderItemRepository', 'update failed: item not found', error)
      throw error
    }

    const originalId = currentRow.original_id ?? currentRow.id

    // Prepare new version based on current row + patch.
    // Remove server-managed columns so Supabase can generate them.
    const base = { ...(currentRow as unknown as Record<string, unknown>) }
    delete base.id
    delete base.created_at
    delete base.updated_at
    delete base.updated_by

    const insertPayload: OrderItemCreateInput = {
      ...(base as OrderItemCreateInput),
      ...(patch as OrderItemCreateInput),
      original_id: originalId,
      updated_by: patch.updated_by ?? null,
      // Insert as inactive first to avoid unique constraint collisions.
      is_active: false,
    }

    const { data: inserted, error: insertError } = await this.supabase
      .from('order_item')
      .insert(insertPayload)
      .select('*')
      .single()

    if (insertError) {
      this.logger.error('SupabaseOrderItemRepository', 'update (insert new version) failed', insertError)
      throw insertError
    }

    const { error: deactivateError } = await this.supabase
      .from('order_item')
      .update({ is_active: false, updated_by: patch.updated_by ?? null })
      .eq('id', itemId)

    if (deactivateError) {
      this.logger.error('SupabaseOrderItemRepository', 'update (deactivate previous) failed', deactivateError)
      throw deactivateError
    }

    const { data: activated, error: activateError } = await this.supabase
      .from('order_item')
      .update({ is_active: true, updated_by: patch.updated_by ?? null })
      .eq('id', (inserted as OrderItemRow).id)
      .select('*')
      .single()

    if (activateError) {
      this.logger.error('SupabaseOrderItemRepository', 'update (activate new version) failed', activateError)
      throw activateError
    }

    return activated as OrderItemRow
  }

  async setSnapshotItemsUpdatedBy(orderId: string, updatedBy: string): Promise<void> {
    const actor = String(updatedBy ?? '').trim()
    if (!actor) return

    const { error } = await this.supabase
      .from('order_item')
      .update({ updated_by: actor })
      .eq('order_id', orderId)
      .is('updated_by', null)

    if (error) {
      this.logger.error('SupabaseOrderItemRepository', 'setSnapshotItemsUpdatedBy failed', error)
      throw error
    }
  }
}
