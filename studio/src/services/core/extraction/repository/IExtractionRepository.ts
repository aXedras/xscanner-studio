import type { IRepository } from '../../../shared/persistence/IRepository'
import type {
  ExtractionCorrectionInput,
  ExtractionListQuery,
  ExtractionRow,
  ExtractionStatusCounts,
  ExtractionCreateInput,
  ExtractionUpdateInput,
} from '../types'
import type { PagedResult } from '../../../shared/persistence/query'

export interface IExtractionRepository extends IRepository<
  ExtractionRow,
  ExtractionCreateInput,
  ExtractionUpdateInput
> {
  findActive(): Promise<ExtractionRow[]>
  findActivePaged(query: ExtractionListQuery): Promise<PagedResult<ExtractionRow>>
  getActiveStatusCounts(input: {
    search?: string
    createdAtFrom?: string
    createdAtTo?: string
  }): Promise<ExtractionStatusCounts>
  findActiveByOriginalId(originalId: string): Promise<ExtractionRow | null>
  findHistoryByOriginalId(originalId: string): Promise<ExtractionRow[]>

  createCorrectionVersion(input: {
    originalId: string
    corrected: ExtractionCorrectionInput
    updatedBy: string
  }): Promise<ExtractionRow>
}
