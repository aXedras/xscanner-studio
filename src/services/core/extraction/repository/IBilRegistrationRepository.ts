import type { BilRegistrationRow } from '../types'

export interface IBilRegistrationRepository {
  findByExtractionId(extractionId: string): Promise<BilRegistrationRow[]>
  findByExtractionIds(extractionIds: string[]): Promise<BilRegistrationRow[]>
}
