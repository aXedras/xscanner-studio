import type { ILogger } from '../../../../lib/utils/logging'
import type { HttpJsonClient } from '../../../infrastructure/http/httpClient'
import type { IBilService } from '../IBilService'
import type { BilRegistrationRow, RegisterOnBilInput, RegisterOnBilResponse } from '../types'

export class HttpBilReadService implements IBilService {
  declare private readonly client: HttpJsonClient
  declare private readonly fallback: IBilService
  declare private readonly logger: ILogger

  constructor(input: { client: HttpJsonClient; fallback: IBilService; logger: ILogger }) {
    this.client = input.client
    this.fallback = input.fallback
    this.logger = input.logger
  }

  async listRegistrationsByExtractionId(extractionId: string): Promise<BilRegistrationRow[]> {
    const id = extractionId.trim()
    if (!id) return []

    const query = new URLSearchParams({ extraction_id: id }).toString()
    const path = `/api/v1/bil/registrations?${query}`
    this.logger.debug('HttpBilReadService', 'listRegistrationsByExtractionId via API', { extractionId: id })
    return await this.client.getJson<BilRegistrationRow[]>(path)
  }

  async listRegistrationsByExtractionIds(extractionIds: string[]): Promise<BilRegistrationRow[]> {
    const ids = extractionIds.map(value => value.trim()).filter(Boolean)
    if (ids.length === 0) return []

    this.logger.debug('HttpBilReadService', 'listRegistrationsByExtractionIds via API', { count: ids.length })
    return await this.client.postJson<BilRegistrationRow[]>('/api/v1/bil/registrations:batch', { extraction_ids: ids })
  }

  async registerOnBil(input: RegisterOnBilInput): Promise<RegisterOnBilResponse> {
    return await this.fallback.registerOnBil(input)
  }
}
