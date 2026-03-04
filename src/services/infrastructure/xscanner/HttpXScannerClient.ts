import type { ILogger } from '../../../lib/utils/logging'
import type { IXScannerClient } from '../../core/xscanner/IXScannerClient'
import type {
  ExtractFromUploadInput,
  ExtractResponse,
  RegisterOnBilInput,
  RegisterOnBilResponse,
} from '../../core/extraction/types'
import type { ExtractOrderFromUploadInput, OrderExtractResponse } from '../../core/order/types'
import { createHttpJsonClient } from '../http/httpClient'

import { getApiBaseUrl } from '../../../lib/runtimeEnv'

const DEFAULT_API_BASE_URL = getApiBaseUrl()

const EXTRACT_UPLOAD_TIMEOUT_MS = 300_000

function buildOrderExtractPath(
  path: string,
  params: {
    strategy: string
    useMock?: boolean
    debug?: boolean
  }
): string {
  // The order upload endpoint uses query params for strategy + debug.
  const search = new URLSearchParams({ strategy: params.strategy })
  if (params.useMock) search.set('use_mock', 'true')
  if (params.debug) search.set('debug', 'true')
  return `${path}?${search.toString()}`
}

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

  async extractOrderFromUpload(input: ExtractOrderFromUploadInput): Promise<OrderExtractResponse> {
    const form = new FormData()

    const files = input.files ?? []
    if (files.length === 0) {
      throw new Error('Missing upload: provide a PDF or one-or-more images')
    }

    const first = files[0]
    const isPdfUpload =
      files.length === 1 &&
      (String(first.type || '').toLowerCase() === 'application/pdf' || first.name.toLowerCase().endsWith('.pdf'))

    if (isPdfUpload) {
      form.append('file', first)
    } else {
      for (const f of files) form.append('files', f)
    }

    const path = buildOrderExtractPath('/order/extract/upload', { strategy: input.strategy, useMock: input.useMock })
    return await this.client.postFormData<OrderExtractResponse>(path, form, {
      timeoutMs: EXTRACT_UPLOAD_TIMEOUT_MS,
    })
  }

  async extractOrderFromUploadDebug(input: ExtractOrderFromUploadInput): Promise<OrderExtractResponse> {
    const form = new FormData()

    const files = input.files ?? []
    if (files.length === 0) {
      throw new Error('Missing upload: provide a PDF or one-or-more images')
    }

    const first = files[0]
    const isPdfUpload =
      files.length === 1 &&
      (String(first.type || '').toLowerCase() === 'application/pdf' || first.name.toLowerCase().endsWith('.pdf'))

    if (isPdfUpload) {
      form.append('file', first)
    } else {
      for (const f of files) form.append('files', f)
    }

    const path = buildOrderExtractPath('/order/extract/upload', {
      strategy: input.strategy,
      useMock: input.useMock,
      debug: true,
    })
    return await this.client.postFormData<OrderExtractResponse>(path, form, {
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
