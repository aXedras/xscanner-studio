import type { BilRegistrationRow, RegisterOnBilInput, RegisterOnBilResponse } from './types'

export interface IBilService {
  listRegistrationsByExtractionId(extractionId: string): Promise<BilRegistrationRow[]>

  listRegistrationsByExtractionIds(extractionIds: string[]): Promise<BilRegistrationRow[]>

  registerOnBil(input: RegisterOnBilInput): Promise<RegisterOnBilResponse>
}
