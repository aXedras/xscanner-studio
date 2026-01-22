import type { SupabaseClient } from '@supabase/supabase-js'
import type { ILogger } from '../../../../lib/utils/logging'
import type {
  ExtractedData,
  ExtractionCorrectionInput,
  ExtractionCreateInput,
  ExtractionListQuery,
  ExtractionRow,
  ExtractionStatus,
  ExtractionStatusCounts,
  ExtractionUpdateInput,
} from '../types'
import type { IExtractionRepository } from './IExtractionRepository'
import { SupabaseCrudRepository } from '../../../infrastructure/persistence/SupabaseCrudRepository'
import { normalizePageSpec } from '../../../shared/persistence/query'

function normalizeSearchTerm(search?: string): string | null {
  if (!search) return null
  const trimmed = search.trim()
  if (!trimmed) return null
  // Supabase `.or()` uses commas to separate filters; keep this safe.
  return trimmed.replaceAll(',', ' ')
}

function isUuid(value: string): boolean {
  // Accept canonical UUID formats. Keep it strict to avoid accidental casts.
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

function applyExtractionSearch<T extends { or: (filters: string) => T }>(query: T, search?: string): T {
  const term = normalizeSearchTerm(search)
  if (!term) return query

  const pattern = `%${term}%`

  const filters: string[] = []
  // `original_id` is a uuid column. Only allow exact match when the term is a UUID.
  if (isUuid(term)) {
    filters.push(`original_id.eq.${term}`)
  }

  // Text fields can be searched via ilike.
  filters.push(`serial_number.ilike.${pattern}`)
  filters.push(`metal.ilike.${pattern}`)
  filters.push(`producer.ilike.${pattern}`)
  filters.push(`strategy_used.ilike.${pattern}`)

  return query.or(filters.join(','))
}

function buildCorrectedExtractedData(previous: ExtractedData, corrected: ExtractionCorrectionInput): ExtractedData {
  const next: ExtractedData = { ...previous }

  next.SerialNumber = corrected.serial_number ?? null
  next.Metal = corrected.metal ?? null
  next.Weight = corrected.weight ?? null
  next.WeightUnit = corrected.weight_unit ?? null
  next.Fineness = corrected.fineness ?? null
  next.Producer = corrected.producer ?? null

  return next
}

export class SupabaseExtractionRepository
  extends SupabaseCrudRepository<ExtractionRow, ExtractionCreateInput, ExtractionUpdateInput>
  implements IExtractionRepository
{
  constructor(supabase: SupabaseClient, logger: ILogger) {
    super(supabase, logger, { table: 'extraction' })
  }

  async findActive(): Promise<ExtractionRow[]> {
    const { data, error } = await this.supabase
      .from('extraction')
      .select('*')
      .eq('is_active', true)
      .order('created_at', { ascending: false })

    if (error) {
      this.logger.error('SupabaseExtractionRepository', 'findActive failed', error)
      throw error
    }

    return (data as ExtractionRow[]) ?? []
  }

  async findActivePaged(
    query: ExtractionListQuery
  ): Promise<{ items: ExtractionRow[]; total: number; page: number; pageSize: number }> {
    const { page, pageSize } = normalizePageSpec(query)

    let q = this.supabase.from('extraction').select('*', { count: 'exact' }).eq('is_active', true)

    q = applyCreatedAtRange(q, query)

    if (query.statuses && query.statuses.length > 0) {
      if (query.statuses.length === 1) {
        q = q.eq('status', query.statuses[0])
      } else {
        q = q.in('status', query.statuses)
      }
    }

    q = applyExtractionSearch(q, query.search)

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
      this.logger.error('SupabaseExtractionRepository', 'findActivePaged failed', error)
      throw error
    }

    return {
      items: (data as ExtractionRow[]) ?? [],
      total: count ?? 0,
      page,
      pageSize,
    }
  }

  async getActiveStatusCounts(input: {
    search?: string
    createdAtFrom?: string
    createdAtTo?: string
  }): Promise<ExtractionStatusCounts> {
    const statuses: ExtractionStatus[] = ['pending', 'corrected', 'validated', 'rejected', 'error']

    const fetchCount = async (status: ExtractionStatus): Promise<number> => {
      let q = this.supabase
        .from('extraction')
        .select('id', { count: 'exact', head: true })
        .eq('is_active', true)
        .eq('status', status)

      q = applyCreatedAtRange(q, input)
      q = applyExtractionSearch(q, input.search)

      const { error, count } = await q
      if (error) {
        this.logger.error('SupabaseExtractionRepository', 'getActiveStatusCounts failed', { status, error })
        throw error
      }
      return count ?? 0
    }

    const [pending, corrected, validated, rejected, error] = await Promise.all(statuses.map(fetchCount))
    return { pending, corrected, validated, rejected, error }
  }

  async findActiveByOriginalId(originalId: string): Promise<ExtractionRow | null> {
    const { data, error } = await this.supabase
      .from('extraction')
      .select('*')
      .eq('original_id', originalId)
      .eq('is_active', true)
      .maybeSingle()

    if (error) {
      this.logger.error('SupabaseExtractionRepository', 'findActiveByOriginalId failed', error)
      throw error
    }

    return (data as ExtractionRow | null) ?? null
  }

  async findHistoryByOriginalId(originalId: string): Promise<ExtractionRow[]> {
    const { data, error } = await this.supabase
      .from('extraction')
      .select('*')
      .eq('original_id', originalId)
      .order('created_at', { ascending: false })

    if (error) {
      this.logger.error('SupabaseExtractionRepository', 'findHistoryByOriginalId failed', error)
      throw error
    }

    return (data as ExtractionRow[]) ?? []
  }

  async createCorrectionVersion(input: {
    originalId: string
    corrected: ExtractionCorrectionInput
    updatedBy: string
  }): Promise<ExtractionRow> {
    const { originalId, corrected, updatedBy } = input

    const active = await this.findActiveByOriginalId(originalId)
    if (!active) {
      throw new Error('Active extraction not found')
    }

    const newRow: ExtractionCreateInput = {
      original_id: active.original_id,
      updated_by: updatedBy,
      storage_path: active.storage_path,
      image_filename: active.image_filename,
      strategy_used: active.strategy_used,
      confidence: active.confidence,
      processing_time: active.processing_time,
      serial_number: corrected.serial_number,
      metal: corrected.metal,
      weight: corrected.weight,
      weight_unit: corrected.weight_unit,
      fineness: corrected.fineness,
      producer: corrected.producer,
      extracted_data: buildCorrectedExtractedData(active.extracted_data, corrected),
      status: 'corrected',
      error: active.error,
      is_active: true,
    }

    // Non-transactional but safe-ish for single-user flow.
    // If insert fails after deactivation, attempt re-activation.
    await this.update(active.id, { is_active: false })

    try {
      return await this.create(newRow)
    } catch (error) {
      try {
        await this.update(active.id, { is_active: true })
      } catch (rollbackError) {
        this.logger.error('SupabaseExtractionRepository', 'rollback failed', rollbackError)
      }
      throw error
    }
  }
}
