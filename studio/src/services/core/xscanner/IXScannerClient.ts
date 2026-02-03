import type {
  ExtractFromUploadInput,
  ExtractResponse,
  RegisterOnBilInput,
  RegisterOnBilResponse,
} from '../extraction/types'
import type { ExtractOrderFromUploadInput, OrderExtractResponse } from '../order/types'

export interface IXScannerClient {
  extractFromUpload(input: ExtractFromUploadInput): Promise<ExtractResponse>
  extractOrderFromUpload(input: ExtractOrderFromUploadInput): Promise<OrderExtractResponse>
  extractOrderFromUploadDebug(input: ExtractOrderFromUploadInput): Promise<OrderExtractResponse>
  registerOnBil(input: RegisterOnBilInput): Promise<RegisterOnBilResponse>
}
