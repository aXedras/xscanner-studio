import type { ILogger } from '../../../lib/utils/logging'
import type { IXScannerClient } from '../../core/xscanner/IXScannerClient'
import type {
  ExtractFromUploadInput,
  ExtractResponse,
  RegisterOnBilInput,
  RegisterOnBilResponse,
} from '../../core/extraction/types'
import { createHttpJsonClient } from '../http/httpClient'

import { getRuntimeEnv } from '../../../lib/runtimeEnv'

const DEFAULT_API_BASE_URL =
  (getRuntimeEnv('VITE_API_URL') as string) || (import.meta.env.VITE_API_URL as string) || 'http://localhost:8000'

const EXTRACT_UPLOAD_TIMEOUT_MS = 300_000

export class HttpXScannerClient implements IXScannerClient {
  declare private readonly logger: ILogger
  declare private readonly apiBaseUrl: string
  declare private readonly client: ReturnType<typeof createHttpJsonClient>

  constructor(
    logger: ILogger,
    apiBaseUrl: string = DEFAULT_API_BASE_URL,
    options?: {
      timeoutMs?: number
    }
  ) {
    this.logger = logger
    this.apiBaseUrl = apiBaseUrl
    this.client = createHttpJsonClient({
      baseUrl: this.apiBaseUrl,
      logger: this.logger,
      name: 'HttpXScannerClient',
      timeoutMs: options?.timeoutMs,
    })
  }

  async extractFromUpload(input: ExtractFromUploadInput): Promise<ExtractResponse> {
    const form = new FormData()
    form.append('file', input.file)
    form.append('strategy', input.strategy)
    form.append('use_mock', String(input.useMock))
    form.append('register_on_bil', String(input.registerOnBil))

    return await this.client.postFormData<ExtractResponse>('/extract/upload', form, {
      timeoutMs: EXTRACT_UPLOAD_TIMEOUT_MS,
    })
  }

  async registerOnBil(input: RegisterOnBilInput): Promise<RegisterOnBilResponse> {
    return await this.client.postJson<RegisterOnBilResponse>('/register', {
      extraction_id: input.extractionId,
      structured_data: input.structuredData,
    })
  }
}
