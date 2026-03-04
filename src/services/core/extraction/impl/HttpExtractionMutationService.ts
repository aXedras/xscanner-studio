import type { ILogger } from '../../../../lib/utils/logging'
import type { HttpJsonClient } from '../../../infrastructure/http/httpClient'
import type { PagedResult } from '../../../shared/query/types'
import type { IExtractionService, StoragePreview } from '../IExtractionService'
import type {
  ExtractFromUploadInput,
  ExtractResponse,
  ExtractionCorrectionInput,
  ExtractionListQuery,
  ExtractionRow,
  ExtractionStatusCounts,
} from '../types'

export class HttpExtractionMutationService implements IExtractionService {
  declare private readonly client: HttpJsonClient
  declare private readonly fallback: IExtractionService
  declare private readonly logger: ILogger

  constructor(input: { client: HttpJsonClient; fallback: IExtractionService; logger: ILogger }) {
    this.client = input.client
    this.fallback = input.fallback
    this.logger = input.logger
  }

  async validateActive(input: { originalId: string; updatedBy: string }): Promise<ExtractionRow> {
    const id = input.originalId.trim()
    this.logger.info('HttpExtractionMutationService', 'validateActive via API', { originalId: id })
    return await this.client.postJson<ExtractionRow>(`/api/v1/extractions/${encodeURIComponent(id)}/validate`, {
      updatedBy: input.updatedBy,
    })
  }

  async rejectActive(input: { originalId: string; updatedBy: string }): Promise<ExtractionRow> {
    const id = input.originalId.trim()
    this.logger.info('HttpExtractionMutationService', 'rejectActive via API', { originalId: id })
    return await this.client.postJson<ExtractionRow>(`/api/v1/extractions/${encodeURIComponent(id)}/reject`, {
      updatedBy: input.updatedBy,
    })
  }

  async createCorrectionVersion(input: {
    originalId: string
    corrected: ExtractionCorrectionInput
    updatedBy: string
  }): Promise<ExtractionRow> {
    const id = input.originalId.trim()
    this.logger.info('HttpExtractionMutationService', 'createCorrectionVersion via API', { originalId: id })
    return await this.client.postJson<ExtractionRow>(`/api/v1/extractions/${encodeURIComponent(id)}/corrections`, {
      corrected: input.corrected,
      updatedBy: input.updatedBy,
    })
  }

  async listActive(): Promise<ExtractionRow[]> {
    return await this.fallback.listActive()
  }

  async listActivePaged(query: ExtractionListQuery): Promise<PagedResult<ExtractionRow>> {
    return await this.fallback.listActivePaged(query)
  }

  async getActiveStatusCounts(input: {
    search?: string
    createdAtFrom?: string
    createdAtTo?: string
  }): Promise<ExtractionStatusCounts> {
    return await this.fallback.getActiveStatusCounts(input)
  }

  async getActiveByOriginalId(originalId: string): Promise<ExtractionRow | null> {
    return await this.fallback.getActiveByOriginalId(originalId)
  }

  async getHistoryByOriginalId(originalId: string): Promise<ExtractionRow[]> {
    return await this.fallback.getHistoryByOriginalId(originalId)
  }

  async getImagePreviewSrc(storagePath: string): Promise<StoragePreview | null> {
    return await this.fallback.getImagePreviewSrc(storagePath)
  }

  async extractFromUpload(input: ExtractFromUploadInput): Promise<ExtractResponse> {
    return await this.fallback.extractFromUpload(input)
  }
}
