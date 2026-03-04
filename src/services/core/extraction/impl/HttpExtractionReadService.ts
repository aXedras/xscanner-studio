import type { ILogger } from '../../../../lib/utils/logging'
import type { HttpJsonClient } from '../../../infrastructure/http/httpClient'
import type { PagedResult } from '../../../shared/query/types'
import { isHttpNotFound } from '../../../shared/http/errors'
import { toPagedResult } from '../../../shared/http/pagedResponse'
import { buildPagedListQuery, buildStatusCountQuery, withQuery } from '../../../shared/http/queryParams'
import type { IExtractionService, StoragePreview } from '../IExtractionService'
import type {
  ExtractFromUploadInput,
  ExtractResponse,
  ExtractionCorrectionInput,
  ExtractionListQuery,
  ExtractionRow,
  ExtractionStatusCounts,
} from '../types'

type PagedExtractionResponse = {
  items: ExtractionRow[]
  total: number
  page: number
  page_size: number
}

type StoragePreviewResponse = {
  signed_url?: string | null
  signedUrl?: string | null
  preview_url?: string | null
  previewUrl?: string | null
  url?: string | null
  src?: string | null
}

export class HttpExtractionReadService implements IExtractionService {
  declare private readonly client: HttpJsonClient
  declare private readonly fallback: IExtractionService
  declare private readonly logger: ILogger

  constructor(input: { client: HttpJsonClient; fallback: IExtractionService; logger: ILogger }) {
    this.client = input.client
    this.fallback = input.fallback
    this.logger = input.logger
  }

  async listActivePaged(query: ExtractionListQuery): Promise<PagedResult<ExtractionRow>> {
    const requestPath = withQuery('/api/v1/extractions', buildPagedListQuery(query))
    const response = await this.client.getJson<PagedExtractionResponse>(requestPath)
    return toPagedResult(response, 'Extractions list response')
  }

  async getActiveStatusCounts(input: {
    search?: string
    createdAtFrom?: string
    createdAtTo?: string
  }): Promise<ExtractionStatusCounts> {
    const requestPath = withQuery('/api/v1/extractions/status-counts', buildStatusCountQuery(input))
    return await this.client.getJson<ExtractionStatusCounts>(requestPath)
  }

  async getActiveByOriginalId(originalId: string): Promise<ExtractionRow | null> {
    try {
      return await this.client.getJson<ExtractionRow>(
        `/api/v1/extractions/by-original/${encodeURIComponent(originalId)}/active`
      )
    } catch (error) {
      if (isHttpNotFound(error)) return null
      throw error
    }
  }

  async getHistoryByOriginalId(originalId: string): Promise<ExtractionRow[]> {
    try {
      return await this.client.getJson<ExtractionRow[]>(
        `/api/v1/extractions/by-original/${encodeURIComponent(originalId)}/history`
      )
    } catch (error) {
      if (isHttpNotFound(error)) return []
      throw error
    }
  }

  async getImagePreviewSrc(storagePath: string): Promise<StoragePreview | null> {
    const trimmed = storagePath.trim()
    if (!trimmed) return null

    const requestPath = withQuery('/api/v1/storage/preview', new URLSearchParams({ storage_path: trimmed }).toString())
    const response = await this.client.getJson<StoragePreviewResponse>(requestPath)

    const src =
      response.signed_url ??
      response.signedUrl ??
      response.preview_url ??
      response.previewUrl ??
      response.url ??
      response.src ??
      null

    if (src?.trim()) {
      return { src }
    }

    this.logger.warn('HttpExtractionReadService', 'getImagePreviewSrc returned empty preview URL', {
      storagePath: trimmed,
    })
    return null
  }

  async listActive(): Promise<ExtractionRow[]> {
    return await this.fallback.listActive()
  }

  async extractFromUpload(input: ExtractFromUploadInput): Promise<ExtractResponse> {
    return await this.fallback.extractFromUpload(input)
  }

  async validateActive(input: { originalId: string; updatedBy: string }): Promise<ExtractionRow> {
    return await this.fallback.validateActive(input)
  }

  async rejectActive(input: { originalId: string; updatedBy: string }): Promise<ExtractionRow> {
    return await this.fallback.rejectActive(input)
  }

  async createCorrectionVersion(input: {
    originalId: string
    corrected: ExtractionCorrectionInput
    updatedBy: string
  }): Promise<ExtractionRow> {
    return await this.fallback.createCorrectionVersion(input)
  }
}
