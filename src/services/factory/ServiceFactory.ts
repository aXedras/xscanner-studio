import type { IAuthService } from '../core/auth/IAuthService'
import { AuthService } from '../core/auth/impl/AuthService'
import type { IExtractionService } from '../core/extraction/IExtractionService'
import type { IBilService } from '../core/extraction/IBullionIntegrityLedgerService'
import { HttpBilReadService } from '../core/extraction/impl/HttpBilReadService'
import { HttpExtractionMutationService } from '../core/extraction/impl/HttpExtractionMutationService'
import { HttpExtractionReadService } from '../core/extraction/impl/HttpExtractionReadService'
import type { IOrderService, StoragePreview } from '../core/order/IOrderService'
import { HttpOrderReadService } from '../core/order/impl/HttpOrderReadService'
import type { IXScannerClient } from '../core/xscanner/IXScannerClient'
import type {
  ExtractFromUploadInput,
  ExtractResponse,
  ExtractionRow,
  ExtractionStatusCounts,
  RegisterOnBilInput,
  RegisterOnBilResponse,
} from '../core/extraction/types'
import type {
  ExtractOrderFromUploadInput,
  OrderExtractResponse,
  OrderItemRow,
  OrderRow,
  OrderStatusCounts,
} from '../core/order/types'
import { createHttpJsonClient, joinUrl } from '../infrastructure/http/httpClient'
import { HttpXScannerClient } from '../infrastructure/xscanner/HttpXScannerClient'
import type { PagedResult } from '../shared/query/types'
import { getApiBaseUrl, getRuntimeEnv } from '../../lib/runtimeEnv'
import type { ILogger } from '../../lib/utils/logging'
import type { ServiceContainer } from './ServiceContainer'

function isEnabled(value: string | undefined): boolean {
  const normalized = (value ?? '').trim().toLowerCase()
  return normalized === '1' || normalized === 'true' || normalized === 'yes' || normalized === 'on'
}

function readEnvVar(name: string): string | undefined {
  const runtimeValue = getRuntimeEnv(name)
  if (runtimeValue) return runtimeValue

  switch (name) {
    case 'VITE_API_URL':
      return import.meta.env.VITE_API_URL as string | undefined
    case 'VITE_USE_AUTH_API':
      return import.meta.env.VITE_USE_AUTH_API as string | undefined
    case 'VITE_USE_ORDERS_READ_API':
      return import.meta.env.VITE_USE_ORDERS_READ_API as string | undefined
    case 'VITE_USE_EXTRACTIONS_READ_API':
      return import.meta.env.VITE_USE_EXTRACTIONS_READ_API as string | undefined
    case 'VITE_USE_BIL_READ_API':
      return import.meta.env.VITE_USE_BIL_READ_API as string | undefined
    case 'VITE_USE_EXTRACTIONS_MUTATION_API':
      return import.meta.env.VITE_USE_EXTRACTIONS_MUTATION_API as string | undefined
    default:
      return undefined
  }
}

function requireApiBaseUrl(): string {
  return getApiBaseUrl()
}

function unsupported(method: string): never {
  throw new Error(`${method} is not available in API-only mode yet.`)
}

export class ServiceFactory {
  private static instance: ServiceFactory | null = null

  private readonly _authService: IAuthService
  private readonly _extractionService: IExtractionService
  private readonly _bilService: IBilService
  private readonly _orderService: IOrderService
  private readonly _xscannerClient: IXScannerClient
  private readonly _logger: ILogger

  private constructor(container: ServiceContainer) {
    this._logger = container.logger
    const useAuthApi = isEnabled(readEnvVar('VITE_USE_AUTH_API'))
    const useOrdersReadApi = isEnabled(readEnvVar('VITE_USE_ORDERS_READ_API'))
    const useExtractionsReadApi = isEnabled(readEnvVar('VITE_USE_EXTRACTIONS_READ_API'))
    const useBilReadApi = isEnabled(readEnvVar('VITE_USE_BIL_READ_API'))
    const useExtractionsMutationApi = isEnabled(readEnvVar('VITE_USE_EXTRACTIONS_MUTATION_API'))

    const apiBaseUrl = requireApiBaseUrl()

    const createApiClient = (name: string) => {
      return createHttpJsonClient({
        baseUrl: apiBaseUrl,
        logger: container.logger,
        name,
        credentials: 'include',
      })
    }

    const resolvePreviewSrc = (storagePath: string): StoragePreview | null => {
      const trimmed = storagePath.trim()
      if (!trimmed) return null
      const src = /^https?:\/\//i.test(trimmed) ? trimmed : joinUrl(apiBaseUrl, trimmed)
      return { src }
    }

    this._authService = new AuthService({
      client: createApiClient('AuthApiClient'),
      logger: container.logger,
    })

    this._xscannerClient = new HttpXScannerClient(container.logger, apiBaseUrl)

    const bilServiceBase: IBilService = {
      listRegistrationsByExtractionId: async (): Promise<import('../core/extraction/types').BilRegistrationRow[]> => [],
      listRegistrationsByExtractionIds: async (): Promise<
        import('../core/extraction/types').BilRegistrationRow[]
      > => [],
      registerOnBil: async (input: RegisterOnBilInput): Promise<RegisterOnBilResponse> => {
        return await this._xscannerClient.registerOnBil(input)
      },
    }

    this._bilService = new HttpBilReadService({
      client: createApiClient('BilReadApiClient'),
      fallback: bilServiceBase,
      logger: container.logger,
    })

    const extractionReadClient = createApiClient('ExtractionsReadApiClient')
    const extractionServiceBase: IExtractionService = {
      listActive: async (): Promise<ExtractionRow[]> => {
        const response = await extractionReadClient.getJson<{ items: ExtractionRow[] }>(
          '/api/v1/extractions?page=1&page_size=200&sort_field=created_at&sort_direction=desc'
        )
        return response.items ?? []
      },
      listActivePaged: async (): Promise<PagedResult<ExtractionRow>> =>
        unsupported('extractionService.listActivePaged'),
      getActiveStatusCounts: async (): Promise<ExtractionStatusCounts> =>
        unsupported('extractionService.getActiveStatusCounts'),
      getActiveByOriginalId: async (): Promise<ExtractionRow | null> =>
        unsupported('extractionService.getActiveByOriginalId'),
      getHistoryByOriginalId: async (): Promise<ExtractionRow[]> =>
        unsupported('extractionService.getHistoryByOriginalId'),
      getImagePreviewSrc: async () => unsupported('extractionService.getImagePreviewSrc'),
      extractFromUpload: async (input: ExtractFromUploadInput): Promise<ExtractResponse> => {
        return await this._xscannerClient.extractFromUpload(input)
      },
      validateActive: async (): Promise<ExtractionRow> => unsupported('extractionService.validateActive'),
      rejectActive: async (): Promise<ExtractionRow> => unsupported('extractionService.rejectActive'),
      createCorrectionVersion: async (): Promise<ExtractionRow> =>
        unsupported('extractionService.createCorrectionVersion'),
    }

    const extractionReadService = new HttpExtractionReadService({
      client: extractionReadClient,
      fallback: extractionServiceBase,
      logger: container.logger,
    })

    this._extractionService = new HttpExtractionMutationService({
      client: createApiClient('ExtractionsMutationApiClient'),
      fallback: extractionReadService,
      logger: container.logger,
    })

    const orderServiceBase: IOrderService = {
      extractFromUpload: async (input: ExtractOrderFromUploadInput): Promise<OrderExtractResponse> => {
        return await this._xscannerClient.extractOrderFromUpload(input)
      },
      extractFromUploadDebug: async (input: ExtractOrderFromUploadInput): Promise<OrderExtractResponse> => {
        return await this._xscannerClient.extractOrderFromUploadDebug(input)
      },
      attributePersistedSnapshot: async (): Promise<void> => {},
      listActivePaged: async (): Promise<{
        items: OrderRow[]
        total: number
        page: number
        pageSize: number
      }> => unsupported('orderService.listActivePaged'),
      getActiveStatusCounts: async (): Promise<OrderStatusCounts> => unsupported('orderService.getActiveStatusCounts'),
      findActiveByOriginalId: async (): Promise<OrderRow | null> => unsupported('orderService.findActiveByOriginalId'),
      findHistoryByOriginalId: async (): Promise<OrderRow[]> => unsupported('orderService.findHistoryByOriginalId'),
      updateOrder: async (): Promise<OrderRow> => unsupported('orderService.updateOrder'),
      resolveOriginalIdByOrderId: async (): Promise<string | null> => null,
      listActiveItems: async (): Promise<OrderItemRow[]> => [],
      listActiveItemsByOriginalId: async (): Promise<OrderItemRow[]> => [],
      findItemHistoryByOriginalId: async (): Promise<OrderItemRow[]> => [],
      createItem: async (): Promise<OrderItemRow> => unsupported('orderService.createItem'),
      updateItem: async (): Promise<OrderItemRow> => unsupported('orderService.updateItem'),
      deleteItem: async (): Promise<void> => unsupported('orderService.deleteItem'),
      getPdfPreviewSrc: async (storagePath: string): Promise<StoragePreview | null> => {
        return resolvePreviewSrc(storagePath)
      },
    }

    this._orderService = new HttpOrderReadService({
      client: createApiClient('OrdersReadApiClient'),
      fallback: orderServiceBase,
      logger: container.logger,
    })

    container.logger.info('ServiceFactory', 'API-only services configured', {
      baseUrl: apiBaseUrl,
      useOrdersReadApi,
      useExtractionsReadApi,
      useBilReadApi,
      useExtractionsMutationApi,
      useAuthApi,
    })
  }

  static getInstance(container: ServiceContainer): ServiceFactory {
    ServiceFactory.instance ??= new ServiceFactory(container)
    return ServiceFactory.instance
  }

  get authService(): IAuthService {
    return this._authService
  }

  get extractionService(): IExtractionService {
    return this._extractionService
  }

  get bilService(): IBilService {
    return this._bilService
  }

  get orderService(): IOrderService {
    return this._orderService
  }

  get xscannerClient(): IXScannerClient {
    return this._xscannerClient
  }

  get logger(): ILogger {
    return this._logger
  }
}
