import type {
  ExtractFromUploadInput,
  ExtractResponse,
  RegisterOnBilInput,
  RegisterOnBilResponse,
} from '../extraction/types'

export interface IXScannerClient {
  extractFromUpload(input: ExtractFromUploadInput): Promise<ExtractResponse>
  registerOnBil(input: RegisterOnBilInput): Promise<RegisterOnBilResponse>
}
