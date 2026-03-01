import type { ILogger } from '../../../../lib/utils/logging'
import type { IExtractionService } from '../IExtractionService'
import type { IExtractionRepository } from '../repository/IExtractionRepository'
import type {
  ExtractFromUploadInput,
  ExtractResponse,
  ExtractionCorrectionInput,
  ExtractionListQuery,
  ExtractionRow,
  ExtractionStatus,
  ExtractionStatusCounts,
} from '../types'
import type { PagedResult } from '../../../shared/persistence/query'
import type { IXScannerClient } from '../../xscanner/IXScannerClient'
import type { IBilService } from '../IBilService'

async function updateActiveStatus(input: {
  repository: IExtractionRepository
  originalId: string
  status: ExtractionStatus
  updatedBy: string
}): Promise<ExtractionRow> {
  const active = await input.repository.findActiveByOriginalId(input.originalId)
  if (!active) {
    throw new Error(`Active extraction not found for originalId: ${input.originalId}`)
  }

  return await input.repository.update(String(active.id), {
    status: input.status,
    updated_by: input.updatedBy,
  })
}

export class ExtractionService implements IExtractionService {
  declare private readonly repository: IExtractionRepository
  declare private readonly xscannerClient: IXScannerClient
  declare private readonly bilService: IBilService
  declare private readonly logger: ILogger

  constructor(
    repository: IExtractionRepository,
    xscannerClient: IXScannerClient,
    bilService: IBilService,
    logger: ILogger
  ) {
    this.repository = repository
    this.xscannerClient = xscannerClient
    this.bilService = bilService
    this.logger = logger
  }

  async listActive(): Promise<ExtractionRow[]> {
    this.logger.debug('ExtractionService', 'listActive')
    return await this.repository.findActive()
  }

  async listActivePaged(query: ExtractionListQuery): Promise<PagedResult<ExtractionRow>> {
    this.logger.debug('ExtractionService', 'listActivePaged', {
      page: query.page,
      pageSize: query.pageSize,
      sort: query.sort,
      hasSearch: Boolean(query.search && query.search.trim()),
      createdAtFrom: query.createdAtFrom,
      createdAtTo: query.createdAtTo,
      statuses: query.statuses,
    })

    return await this.repository.findActivePaged(query)
  }

  async getActiveStatusCounts(input: {
    search?: string
    createdAtFrom?: string
    createdAtTo?: string
  }): Promise<ExtractionStatusCounts> {
    this.logger.debug('ExtractionService', 'getActiveStatusCounts', {
      hasSearch: Boolean(input.search && input.search.trim()),
      createdAtFrom: input.createdAtFrom,
      createdAtTo: input.createdAtTo,
    })

    return await this.repository.getActiveStatusCounts(input)
  }

  async getActiveByOriginalId(originalId: string): Promise<ExtractionRow | null> {
    this.logger.debug('ExtractionService', 'getActiveByOriginalId', { originalId })
    return await this.repository.findActiveByOriginalId(originalId)
  }

  async getHistoryByOriginalId(originalId: string): Promise<ExtractionRow[]> {
    this.logger.debug('ExtractionService', 'getHistoryByOriginalId', { originalId })
    return await this.repository.findHistoryByOriginalId(originalId)
  }

  async extractFromUpload(input: ExtractFromUploadInput): Promise<ExtractResponse> {
    this.logger.info('ExtractionService', 'extractFromUpload', {
      strategy: input.strategy,
      useMock: input.useMock,
      registerOnBil: input.registerOnBil,
      fileName: input.file?.name,
      fileSize: input.file?.size,
    })

    const result = await this.xscannerClient.extractFromUpload(input)

    this.logger.info('ExtractionService', 'extractFromUpload result', {
      success: result.success,
      requestId: result.request_id,
      confidence: result.confidence,
      processingTime: result.processing_time,
      strategyUsed: result.strategy_used,
      extractionId: result.extraction_id,
      hasError: Boolean(result.error),
      hasRegistration: Boolean(result.registration),
    })

    return result
  }

  async validateActive(input: { originalId: string; updatedBy: string }): Promise<ExtractionRow> {
    this.logger.info('ExtractionService', 'validateActive', {
      originalId: input.originalId,
      hasUpdatedBy: Boolean(input.updatedBy),
    })

    const active = await this.repository.findActiveByOriginalId(input.originalId)
    if (!active) {
      throw new Error(`Active extraction not found for originalId: ${input.originalId}`)
    }

    const result = await this.bilService.registerOnBil({
      extractionId: String(active.id),
      structuredData: active.extracted_data as unknown as Record<string, unknown>,
    })

    if (!result.success) {
      throw new Error(result.error ?? result.details ?? 'Registration failed')
    }

    const updated = await updateActiveStatus({
      repository: this.repository,
      originalId: input.originalId,
      status: 'validated',
      updatedBy: input.updatedBy,
    })

    this.logger.info('ExtractionService', 'validateActive status updated', {
      originalId: input.originalId,
      status: updated.status,
      updatedBy: updated.updated_by,
    })

    return updated
  }

  async rejectActive(input: { originalId: string; updatedBy: string }): Promise<ExtractionRow> {
    this.logger.info('ExtractionService', 'rejectActive', {
      originalId: input.originalId,
      hasUpdatedBy: Boolean(input.updatedBy),
    })

    const updated = await updateActiveStatus({
      repository: this.repository,
      originalId: input.originalId,
      status: 'rejected',
      updatedBy: input.updatedBy,
    })

    this.logger.info('ExtractionService', 'rejectActive status updated', {
      originalId: input.originalId,
      status: updated.status,
      updatedBy: updated.updated_by,
    })

    return updated
  }

  async createCorrectionVersion(input: {
    originalId: string
    corrected: ExtractionCorrectionInput
    updatedBy: string
  }): Promise<ExtractionRow> {
    this.logger.info('ExtractionService', 'createCorrectionVersion', {
      originalId: input.originalId,
      hasUpdatedBy: Boolean(input.updatedBy),
    })

    const updated = await this.repository.createCorrectionVersion(input)

    this.logger.info('ExtractionService', 'createCorrectionVersion created', {
      originalId: input.originalId,
      status: updated.status,
      updatedBy: updated.updated_by,
    })

    return updated
  }
}
