import type { SupabaseClient } from '@supabase/supabase-js'
import type { ILogger } from '../../lib/utils/logging'

export interface ServiceContainer {
  supabase: SupabaseClient
  logger: ILogger
}
