import type { Json, Tables, TablesInsert, TablesUpdate } from '../../../../lib/supabase/database.types'
import type { PageSpec, SortSpec } from '../../../shared/persistence/query'

export type ExtractionStatus = Tables<'extraction'>['status']

export function getExtractionStatusLabelKey(status: ExtractionStatus): string {
  switch (status) {
    case 'pending':
      return 'extraction.list.stats.pending'
    case 'corrected':
      return 'extraction.list.stats.corrected'
    case 'validated':
      return 'extraction.list.stats.validated'
    case 'rejected':
      return 'extraction.list.stats.rejected'
    case 'error':
      return 'common.status.error'
    default: {
      const _exhaustiveCheck: never = status
      return _exhaustiveCheck
    }
  }
}

export type ExtractedData = { [key: string]: Json | undefined }

export type BilRegistrationRow = Tables<'bil_registration'>

export type ExtractionRow = Omit<Tables<'extraction'>, 'extracted_data'> & {
  extracted_data: ExtractedData
}

export type ExtractionCreateInput = Omit<TablesInsert<'extraction'>, 'extracted_data' | 'status'> & {
  extracted_data?: ExtractedData
  status?: ExtractionStatus
}

export type ExtractionUpdateInput = TablesUpdate<'extraction'>

export interface ExtractionCorrectionInput {
  serial_number: string | null
  metal: string | null
  weight: string | null
  weight_unit: string | null
  fineness: string | null
  producer: string | null
}

export type StrategyChoice = 'local' | 'cloud'

export type ExtractionListSortField =
  | 'created_at'
  | 'status'
  | 'serial_number'
  | 'metal'
  | 'producer'
  | 'strategy_used'
  | 'confidence'

export type ExtractionListQuery = PageSpec & {
  sort?: SortSpec<ExtractionListSortField>
  search?: string
  createdAtFrom?: string
  createdAtTo?: string
  statuses?: ExtractionStatus[]
}

export type ExtractionStatusCounts = {
  pending: number
  corrected: number
  validated: number
  rejected: number
  error: number
}

export type ExtractFromUploadInput = {
  file: File
  strategy: StrategyChoice
  useMock: boolean
  registerOnBil: boolean
}

export interface ExtractResponse {
  success: boolean
  request_id: string
  structured_data: Record<string, unknown>
  extraction_id?: string | null
  confidence: number
  processing_time: number
  strategy_used: string
  error: string | null
  registration?: Record<string, unknown> | null
}

export type RegisterOnBilInput = {
  extractionId: string
  structuredData: Record<string, unknown>
}

export type RegisterOnBilResponse = {
  success: boolean
  registration_id: string | null
  certificate_id: string | null
  error: string | null
  details: string | null
  payload_sent: Record<string, unknown> | null
}
