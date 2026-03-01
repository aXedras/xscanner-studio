import type { SupabaseClient } from '@supabase/supabase-js'
import type { ILogger } from '../../../../lib/utils/logging'
import type {
  OrderCreateInput,
  OrderListQuery,
  OrderRow,
  OrderStatus,
  OrderStatusCounts,
  OrderUpdateInput,
} from '../types'
import type { IOrderRepository } from './IOrderRepository'
import { SupabaseCrudRepository } from '../../../infrastructure/persistence/SupabaseCrudRepository'
import { normalizePageSpec } from '../../../shared/persistence/query'

function normalizeSearchTerm(search?: string): string | null {
  if (!search) return null
  const trimmed = search.trim()
  if (!trimmed) return null
  return trimmed.replaceAll(',', ' ')
}

function isUuid(value: string): boolean {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value)
}

function toIsoStartOfDay(date: string): string {
  return new Date(`${date}T00:00:00.000Z`).toISOString()
}

function toIsoEndOfDay(date: string): string {
  return new Date(`${date}T23:59:59.999Z`).toISOString()
}

function applyCreatedAtRange<
  T extends {
    gte: (column: string, value: string) => T
    lte: (column: string, value: string) => T
  },
>(query: T, input: { createdAtFrom?: string; createdAtTo?: string }): T {
  let next = query
  if (input.createdAtFrom) {
    next = next.gte('created_at', toIsoStartOfDay(input.createdAtFrom))
  }
  if (input.createdAtTo) {
    next = next.lte('created_at', toIsoEndOfDay(input.createdAtTo))
  }
  return next
}

function applyOrderSearch<T extends { or: (filters: string) => T }>(query: T, search?: string): T {
  const term = normalizeSearchTerm(search)
  if (!term) return query

  const pattern = `%${term}%`

  const filters: string[] = []

  if (isUuid(term)) {
    filters.push(`original_id.eq.${term}`)
    filters.push(`id.eq.${term}`)
  }

  filters.push(`document_issuer.ilike.${pattern}`)
  filters.push(`document_number.ilike.${pattern}`)
  filters.push(`order_number.ilike.${pattern}`)
  filters.push(`seller_name.ilike.${pattern}`)
  filters.push(`buyer_name.ilike.${pattern}`)

  return query.or(filters.join(','))
}

export class SupabaseOrderRepository
  extends SupabaseCrudRepository<OrderRow, OrderCreateInput, OrderUpdateInput>
  implements IOrderRepository
{
  constructor(supabase: SupabaseClient, logger: ILogger) {
    super(supabase, logger, { table: 'order' })
  }

  override async update(orderId: string, patch: OrderUpdateInput): Promise<OrderRow> {
    // Versioned updates: create a new version row and deactivate the previous one.
    // We insert the new row as inactive first to avoid unique constraint collisions
    // on (original_id) and document identity (active rows).
    const { data: current, error: loadError } = await this.supabase.from('order').select('*').eq('id', orderId).single()

    if (loadError) {
      this.logger.error('SupabaseOrderRepository', 'update (load current) failed', loadError)
      throw loadError
    }

    const currentRow = (current as OrderRow) ?? null
    if (!currentRow) {
      const error = new Error('Order not found')
      this.logger.error('SupabaseOrderRepository', 'update failed: order not found', error)
      throw error
    }

    const originalId = currentRow.original_id ?? currentRow.id
    const actor = (patch as unknown as { updated_by?: string | null }).updated_by ?? null
    const desiredIsActive = (patch as unknown as { is_active?: boolean }).is_active ?? true

    const base = { ...(currentRow as unknown as Record<string, unknown>) }
    delete base.id
    delete base.created_at
    delete base.updated_at
    delete base.updated_by

    const insertPayload: OrderCreateInput = {
      ...(base as OrderCreateInput),
      ...(patch as OrderCreateInput),
      original_id: originalId,
      updated_by: actor,
      // Insert inactive first to avoid collisions.
      is_active: false,
    }

    const { data: inserted, error: insertError } = await this.supabase
      .from('order')
      .insert(insertPayload)
      .select('*')
      .single()

    if (insertError) {
      this.logger.error('SupabaseOrderRepository', 'update (insert new version) failed', insertError)
      throw insertError
    }

    const insertedRow = inserted as OrderRow

    const { error: deactivateError } = await this.supabase
      .from('order')
      .update({ is_active: false, updated_by: actor })
      .eq('id', orderId)

    if (deactivateError) {
      this.logger.error('SupabaseOrderRepository', 'update (deactivate previous) failed', deactivateError)
      throw deactivateError
    }

    if (!desiredIsActive) {
      return insertedRow
    }

    const { data: activated, error: activateError } = await this.supabase
      .from('order')
      .update({ is_active: true, updated_by: actor })
      .eq('id', insertedRow.id)
      .select('*')
      .single()

    if (activateError) {
      this.logger.error('SupabaseOrderRepository', 'update (activate new version) failed', activateError)
      throw activateError
    }

    return activated as OrderRow
  }

  async setSnapshotUpdatedBy(orderId: string, updatedBy: string): Promise<void> {
    const actor = String(updatedBy ?? '').trim()
    if (!actor) return

    const { error } = await this.supabase
      .from('order')
      .update({ updated_by: actor })
      .eq('id', orderId)
      .is('updated_by', null)

    if (error) {
      this.logger.error('SupabaseOrderRepository', 'setSnapshotUpdatedBy failed', error)
      throw error
    }
  }

  async findActivePaged(
    query: OrderListQuery
  ): Promise<{ items: OrderRow[]; total: number; page: number; pageSize: number }> {
    const { page, pageSize } = normalizePageSpec(query)

    let q = this.supabase.from('order').select('*', { count: 'exact' }).eq('is_active', true)

    q = applyCreatedAtRange(q, query)

    if (query.statuses && query.statuses.length > 0) {
      if (query.statuses.length === 1) {
        q = q.eq('status', query.statuses[0])
      } else {
        q = q.in('status', query.statuses)
      }
    }

    q = applyOrderSearch(q, query.search)

    const sortField = query.sort?.field ?? 'created_at'
    const sortAscending = query.sort?.direction === 'asc'
    q = q.order(sortField, { ascending: sortAscending, nullsFirst: false })
    if (sortField !== 'created_at') {
      q = q.order('created_at', { ascending: false })
    }

    const from = (page - 1) * pageSize
    const to = from + pageSize - 1

    const { data, error, count } = await q.range(from, to)

    if (error) {
      this.logger.error('SupabaseOrderRepository', 'findActivePaged failed', error)
      throw error
    }

    return {
      items: (data as OrderRow[]) ?? [],
      total: count ?? 0,
      page,
      pageSize,
    }
  }

  async getActiveStatusCounts(input: {
    search?: string
    createdAtFrom?: string
    createdAtTo?: string
  }): Promise<OrderStatusCounts> {
    const statuses: OrderStatus[] = ['pending', 'validated', 'corrected', 'rejected', 'error', 'closed']

    const fetchCount = async (status: OrderStatus): Promise<number> => {
      let q = this.supabase
        .from('order')
        .select('id', { count: 'exact', head: true })
        .eq('is_active', true)
        .eq('status', status)

      q = applyCreatedAtRange(q, input)
      q = applyOrderSearch(q, input.search)

      const { error, count } = await q
      if (error) {
        this.logger.error('SupabaseOrderRepository', 'getActiveStatusCounts failed', { status, error })
        throw error
      }
      return count ?? 0
    }

    const [pending, validated, corrected, rejected, error, closed] = await Promise.all(statuses.map(fetchCount))
    return { pending, validated, corrected, rejected, error, closed }
  }

  async findActiveByOriginalId(originalId: string): Promise<OrderRow | null> {
    const { data, error } = await this.supabase
      .from('order')
      .select('*')
      .eq('original_id', originalId)
      .eq('is_active', true)
      .maybeSingle()

    if (error) {
      this.logger.error('SupabaseOrderRepository', 'findActiveByOriginalId failed', error)
      throw error
    }

    return (data as OrderRow | null) ?? null
  }

  async findHistoryByOriginalId(originalId: string): Promise<OrderRow[]> {
    const { data, error } = await this.supabase
      .from('order')
      .select('*')
      .eq('original_id', originalId)
      .order('created_at', { ascending: false })

    if (error) {
      this.logger.error('SupabaseOrderRepository', 'findHistoryByOriginalId failed', error)
      throw error
    }

    return (data as OrderRow[]) ?? []
  }
}
