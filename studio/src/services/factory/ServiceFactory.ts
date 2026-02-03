import type { IAuthService } from '../core/auth/IAuthService'
import { AuthService } from '../core/auth/impl/AuthService'
import { SupabaseAuthRepository } from '../core/auth/repository/SupabaseAuthRepository'
import type { IExtractionService } from '../core/extraction/IExtractionService'
import { ExtractionService } from '../core/extraction/impl/ExtractionService'
import { SupabaseExtractionRepository } from '../core/extraction/repository/SupabaseExtractionRepository'
import type { IBilService } from '../core/extraction/IBilService'
import { BilService } from '../core/extraction/impl/BilService'
import { SupabaseBilRegistrationRepository } from '../core/extraction/repository/SupabaseBilRegistrationRepository'
import type { IStorageService } from '../core/storage/IStorageService'
import { StorageService } from '../core/storage/impl/StorageService'
import type { IOrderService } from '../core/order/IOrderService'
import { OrderService } from '../core/order/impl/OrderService'
import { SupabaseOrderRepository } from '../core/order/repository/SupabaseOrderRepository'
import { SupabaseOrderItemRepository } from '../core/order/repository/SupabaseOrderItemRepository'
import type { IXScannerClient } from '../core/xscanner/IXScannerClient'
import { HttpXScannerClient } from '../infrastructure/xscanner/HttpXScannerClient'
import type { ILogger } from '../../lib/utils/logging'
import type { ServiceContainer } from './ServiceContainer'

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
    const authRepository = new SupabaseAuthRepository(container.supabase, container.logger)
    this._authService = new AuthService(authRepository, container.logger)

    this._storageService = new StorageService(container.supabase, container.logger)

    this._xscannerClient = new HttpXScannerClient(container.logger)

    const orderRepository = new SupabaseOrderRepository(container.supabase, container.logger)
    const orderItemRepository = new SupabaseOrderItemRepository(container.supabase, container.logger)
    this._orderService = new OrderService(
      orderRepository,
      orderItemRepository,
      this._xscannerClient,
      this._storageService,
      container.logger
    )

    const extractionRepository = new SupabaseExtractionRepository(container.supabase, container.logger)
    const bilRegistrationRepository = new SupabaseBilRegistrationRepository(container.supabase, container.logger)
    this._bilService = new BilService(bilRegistrationRepository, this._xscannerClient, container.logger)

    this._extractionService = new ExtractionService(
      extractionRepository,
      this._xscannerClient,
      this._bilService,
      container.logger
    )
  }

  static getInstance(container: ServiceContainer): ServiceFactory {
    if (!ServiceFactory.instance) {
      ServiceFactory.instance = new ServiceFactory(container)
    }
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
