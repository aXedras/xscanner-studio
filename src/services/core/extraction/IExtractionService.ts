import type {
  ExtractFromUploadInput,
  ExtractResponse,
  ExtractionCorrectionInput,
  ExtractionListQuery,
  ExtractionRow,
  ExtractionStatusCounts,
} from './types'
import type { PagedResult } from '../../shared/query/types'

export type StoragePreview = {
  src: string
  revoke?: () => void
}

export interface IExtractionService {
  listActive(): Promise<ExtractionRow[]>
  listActivePaged(query: ExtractionListQuery): Promise<PagedResult<ExtractionRow>>
  getActiveStatusCounts(input: {
    search?: string
    createdAtFrom?: string
    createdAtTo?: string
  }): Promise<ExtractionStatusCounts>
  getActiveByOriginalId(originalId: string): Promise<ExtractionRow | null>
  getHistoryByOriginalId(originalId: string): Promise<ExtractionRow[]>
  getImagePreviewSrc(storagePath: string): Promise<StoragePreview | null>

  extractFromUpload(input: ExtractFromUploadInput): Promise<ExtractResponse>

  validateActive(input: { originalId: string; updatedBy: string }): Promise<ExtractionRow>
  rejectActive(input: { originalId: string; updatedBy: string }): Promise<ExtractionRow>

  createCorrectionVersion(input: {
    originalId: string
    corrected: ExtractionCorrectionInput
    updatedBy: string
  }): Promise<ExtractionRow>
}
