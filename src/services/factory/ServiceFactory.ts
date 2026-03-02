import type { IAuthService } from '../core/auth/IAuthService'
import { AuthService } from '../core/auth/impl/AuthService'
import { HttpAuthRepository } from '../core/auth/repository/HttpAuthRepository'
import { SupabaseAuthRepository } from '../core/auth/repository/SupabaseAuthRepository'
import type { IExtractionService } from '../core/extraction/IExtractionService'
import { ExtractionService } from '../core/extraction/impl/ExtractionService'
import { HttpBilReadService } from '../core/extraction/impl/HttpBilReadService'
import { HttpExtractionMutationService } from '../core/extraction/impl/HttpExtractionMutationService'
import { HttpExtractionReadService } from '../core/extraction/impl/HttpExtractionReadService'
import { SupabaseExtractionRepository } from '../core/extraction/repository/SupabaseExtractionRepository'
import type { IBilService } from '../core/extraction/IBilService'
import { BilService } from '../core/extraction/impl/BilService'
import { SupabaseBilRegistrationRepository } from '../core/extraction/repository/SupabaseBilRegistrationRepository'
import type { IStorageService } from '../core/storage/IStorageService'
import { StorageService } from '../core/storage/impl/StorageService'
import type { IOrderService } from '../core/order/IOrderService'
import { HttpOrderReadService } from '../core/order/impl/HttpOrderReadService'
import { OrderService } from '../core/order/impl/OrderService'
import { SupabaseOrderRepository } from '../core/order/repository/SupabaseOrderRepository'
import { SupabaseOrderItemRepository } from '../core/order/repository/SupabaseOrderItemRepository'
import type { IXScannerClient } from '../core/xscanner/IXScannerClient'
import { HttpXScannerClient } from '../infrastructure/xscanner/HttpXScannerClient'
import { createHttpJsonClient } from '../infrastructure/http/httpClient'
import type { ILogger } from '../../lib/utils/logging'
import type { ServiceContainer } from './ServiceContainer'
import { getRuntimeEnv } from '../../lib/runtimeEnv'

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
  const raw = readEnvVar('VITE_API_URL')
  const trimmed = (raw ?? '').trim()
  if (!trimmed) {
    throw new Error('VITE_API_URL is required when API adapters are enabled.')
  }
  return trimmed
}

export class ServiceFactory {
  private static instance: ServiceFactory | null = null

  private readonly _authService: IAuthService
  private readonly _extractionService: IExtractionService
  private readonly _bilService: IBilService
  private readonly _storageService: IStorageService
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

    const usesApiAdapter =
      useAuthApi || useOrdersReadApi || useExtractionsReadApi || useBilReadApi || useExtractionsMutationApi

    const apiBaseUrl = usesApiAdapter ? requireApiBaseUrl() : null

    const createApiClient = (name: string) => {
      if (!apiBaseUrl) {
        throw new Error(`API client '${name}' cannot be created without a configured API base URL.`)
      }

      return createHttpJsonClient({
        baseUrl: apiBaseUrl,
        logger: container.logger,
        name,
      })
    }

    const authRepository = useAuthApi
      ? new HttpAuthRepository({
          client: createApiClient('AuthApiClient'),
          logger: container.logger,
        })
      : new SupabaseAuthRepository(container.supabase, container.logger)

    this._authService = new AuthService(authRepository, container.logger)

    if (useAuthApi) {
      container.logger.info('ServiceFactory', 'Auth API adapter enabled', { baseUrl: apiBaseUrl })
    }

    this._storageService = new StorageService(container.supabase, container.logger)

    this._xscannerClient = new HttpXScannerClient(container.logger)

    const orderRepository = new SupabaseOrderRepository(container.supabase, container.logger)
    const orderItemRepository = new SupabaseOrderItemRepository(container.supabase, container.logger)

    const orderServiceBase = new OrderService(
      orderRepository,
      orderItemRepository,
      this._xscannerClient,
      this._storageService,
      container.logger
    )

    this._orderService = useOrdersReadApi
      ? new HttpOrderReadService({
          client: createApiClient('OrdersReadApiClient'),
          fallback: orderServiceBase,
          logger: container.logger,
        })
      : orderServiceBase

    if (useOrdersReadApi) {
      container.logger.info('ServiceFactory', 'Orders read API adapter enabled', { baseUrl: apiBaseUrl })
    }

    const extractionRepository = new SupabaseExtractionRepository(container.supabase, container.logger)
    const bilRegistrationRepository = new SupabaseBilRegistrationRepository(container.supabase, container.logger)

    const bilServiceBase = new BilService(bilRegistrationRepository, this._xscannerClient, container.logger)

    this._bilService = useBilReadApi
      ? new HttpBilReadService({
          client: createApiClient('BilReadApiClient'),
          fallback: bilServiceBase,
          logger: container.logger,
        })
      : bilServiceBase

    const extractionServiceBase = new ExtractionService(
      extractionRepository,
      this._xscannerClient,
      this._bilService,
      container.logger
    )

    const extractionReadService = useExtractionsReadApi
      ? new HttpExtractionReadService({
          client: createApiClient('ExtractionsReadApiClient'),
          fallback: extractionServiceBase,
          logger: container.logger,
        })
      : extractionServiceBase

    if (useExtractionsReadApi) {
      container.logger.info('ServiceFactory', 'Extractions read API adapter enabled', { baseUrl: apiBaseUrl })
    }

    if (useBilReadApi) {
      container.logger.info('ServiceFactory', 'BIL read API adapter enabled', { baseUrl: apiBaseUrl })
    }

    this._extractionService = useExtractionsMutationApi
      ? new HttpExtractionMutationService({
          client: createApiClient('ExtractionsMutationApiClient'),
          fallback: extractionReadService,
          logger: container.logger,
        })
      : extractionReadService

    if (useExtractionsMutationApi) {
      container.logger.info('ServiceFactory', 'Extractions mutation API adapter enabled', {
        baseUrl: apiBaseUrl,
      })
    }
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

  get storageService(): IStorageService {
    return this._storageService
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
