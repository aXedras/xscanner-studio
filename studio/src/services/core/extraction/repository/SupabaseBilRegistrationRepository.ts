import type { SupabaseClient } from '@supabase/supabase-js'
import type { ILogger } from '../../../../lib/utils/logging'
import type { BilRegistrationRow } from '../types'
import type { IBilRegistrationRepository } from './IBilRegistrationRepository'

export class SupabaseBilRegistrationRepository implements IBilRegistrationRepository {
  declare private readonly supabase: SupabaseClient
  declare private readonly logger: ILogger

  constructor(supabase: SupabaseClient, logger: ILogger) {
    this.supabase = supabase
    this.logger = logger
  }

  async findByExtractionId(extractionId: string): Promise<BilRegistrationRow[]> {
    const { data, error } = await this.supabase
      .from('bil_registration')
      .select('*')
      .eq('extraction_id', extractionId)
      .order('created_at', { ascending: false })

    if (error) {
      this.logger.error('SupabaseBilRegistrationRepository', 'findByExtractionId failed', { extractionId, error })
      throw error
    }

    return (data as BilRegistrationRow[]) ?? []
  }

  async findByExtractionIds(extractionIds: string[]): Promise<BilRegistrationRow[]> {
    if (extractionIds.length === 0) return []

    const { data, error } = await this.supabase
      .from('bil_registration')
      .select('*')
      .in('extraction_id', extractionIds)
      .order('created_at', { ascending: false })

    if (error) {
      this.logger.error('SupabaseBilRegistrationRepository', 'findByExtractionIds failed', { extractionIds, error })
      throw error
    }

    return (data as BilRegistrationRow[]) ?? []
  }
}
