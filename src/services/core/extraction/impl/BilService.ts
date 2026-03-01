import type { ILogger } from '../../../../lib/utils/logging'
import type { IBilService } from '../IBilService'
import type { IBilRegistrationRepository } from '../repository/IBilRegistrationRepository'
import type { BilRegistrationRow, RegisterOnBilInput, RegisterOnBilResponse } from '../types'
import type { IXScannerClient } from '../../xscanner/IXScannerClient'

export class BilService implements IBilService {
  declare private readonly repository: IBilRegistrationRepository
  declare private readonly xscannerClient: IXScannerClient
  declare private readonly logger: ILogger

  constructor(repository: IBilRegistrationRepository, xscannerClient: IXScannerClient, logger: ILogger) {
    this.repository = repository
    this.xscannerClient = xscannerClient
    this.logger = logger
  }

  async listRegistrationsByExtractionId(extractionId: string): Promise<BilRegistrationRow[]> {
    this.logger.debug('BilService', 'listRegistrationsByExtractionId', { extractionId })
    return await this.repository.findByExtractionId(extractionId)
  }

  async listRegistrationsByExtractionIds(extractionIds: string[]): Promise<BilRegistrationRow[]> {
    this.logger.debug('BilService', 'listRegistrationsByExtractionIds', { count: extractionIds.length })
    return await this.repository.findByExtractionIds(extractionIds)
  }

  async registerOnBil(input: RegisterOnBilInput): Promise<RegisterOnBilResponse> {
    this.logger.info('BilService', 'registerOnBil', {
      extractionId: input.extractionId,
      hasStructuredData: Boolean(input.structuredData && Object.keys(input.structuredData).length > 0),
    })

    const result = await this.xscannerClient.registerOnBil(input)

    this.logger.info('BilService', 'registerOnBil result', {
      extractionId: input.extractionId,
      success: result.success,
      certificateId: result.certificate_id,
      registrationId: result.registration_id,
      hasError: Boolean(result.error),
      hasDetails: Boolean(result.details),
    })

    return result
  }
}
