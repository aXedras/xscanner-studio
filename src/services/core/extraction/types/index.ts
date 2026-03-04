import type { PageSpec, SortSpec } from '../../../shared/query/types'

export type JsonValue = string | number | boolean | null | { [key: string]: JsonValue | undefined } | JsonValue[]

export type ExtractionStatus = 'pending' | 'validated' | 'corrected' | 'rejected' | 'error'

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

export type ExtractedData = { [key: string]: JsonValue | undefined }

export type BilRegistrationRow = {
  id: string
  extraction_id: string
  trigger_source: string
  success: boolean
  certificate_id: string | null
  processing_time: number | null
  error: string | null
  error_details: JsonValue | null
  http_status: number | null
  endpoint: string | null
  payload_sent: JsonValue | null
  payload_received: JsonValue | null
  created_at: string
}

export type ExtractionRow = {
  id: string
  original_id: string
  updated_by: string | null
  storage_path: string
  image_filename: string | null
  strategy_used: string
  confidence: number | null
  processing_time: number | null
  serial_number: string | null
  metal: string | null
  weight: string | null
  weight_unit: string | null
  fineness: string | null
  producer: string | null
  extracted_data: ExtractedData
  status: ExtractionStatus
  error: string | null
  is_active: boolean
  created_at: string
}

export type ExtractionCreateInput = Partial<ExtractionRow> & {
  original_id: string
  storage_path: string
  strategy_used: string
  extracted_data?: ExtractedData
  status?: ExtractionStatus
}

export type ExtractionUpdateInput = Partial<ExtractionRow>

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
