import type { ILogger } from '../../../../lib/utils/logging'
import type { HttpJsonClient } from '../../../infrastructure/http/httpClient'
import type { IOrderService, StoragePreview } from '../IOrderService'
import { isHttpNotFound } from '../../../shared/http/errors'
import { toPagedResult } from '../../../shared/http/pagedResponse'
import { buildPagedListQuery, buildStatusCountQuery, withQuery } from '../../../shared/http/queryParams'
import type {
  ExtractOrderFromUploadInput,
  OrderExtractResponse,
  OrderItemCreateInput,
  OrderItemRow,
  OrderItemUpdateInput,
  OrderListQuery,
  OrderRow,
  OrderStatusCounts,
  OrderUpdateInput,
} from '../types'

type PagedOrderResponse = {
  items: OrderRow[]
  total: number
  page: number
  page_size: number
}

type StoragePreviewResponse = {
  signed_url?: string | null
  signedUrl?: string | null
  preview_url?: string | null
  previewUrl?: string | null
  url?: string | null
  src?: string | null
}

export class HttpOrderReadService implements IOrderService {
  declare private readonly client: HttpJsonClient
  declare private readonly fallback: IOrderService
  declare private readonly logger: ILogger

  constructor(input: { client: HttpJsonClient; fallback: IOrderService; logger: ILogger }) {
    this.client = input.client
    this.fallback = input.fallback
    this.logger = input.logger
  }

  async listActivePaged(
    query: OrderListQuery
  ): Promise<{ items: OrderRow[]; total: number; page: number; pageSize: number }> {
    const requestPath = withQuery('/api/v1/orders', buildPagedListQuery(query))
    const response = await this.client.getJson<PagedOrderResponse>(requestPath)
    return toPagedResult(response, 'Orders list response')
  }

  async getActiveStatusCounts(input: {
    search?: string
    createdAtFrom?: string
    createdAtTo?: string
  }): Promise<OrderStatusCounts> {
    const requestPath = withQuery('/api/v1/orders/status-counts', buildStatusCountQuery(input))
    return await this.client.getJson<OrderStatusCounts>(requestPath)
  }

  async findActiveByOriginalId(originalId: string): Promise<OrderRow | null> {
    try {
      return await this.client.getJson<OrderRow>(`/api/v1/orders/by-original/${encodeURIComponent(originalId)}/active`)
    } catch (error) {
      if (isHttpNotFound(error)) return null
      throw error
    }
  }

  async findHistoryByOriginalId(originalId: string): Promise<OrderRow[]> {
    try {
      return await this.client.getJson<OrderRow[]>(
        `/api/v1/orders/by-original/${encodeURIComponent(originalId)}/history`
      )
    } catch (error) {
      if (isHttpNotFound(error)) return []
      throw error
    }
  }

  async extractFromUpload(input: ExtractOrderFromUploadInput): Promise<OrderExtractResponse> {
    return await this.fallback.extractFromUpload(input)
  }

  async extractFromUploadDebug(input: ExtractOrderFromUploadInput): Promise<OrderExtractResponse> {
    return await this.fallback.extractFromUploadDebug(input)
  }

  async attributePersistedSnapshot(orderId: string, actorId: string): Promise<void> {
    const id = orderId.trim()
    const updatedBy = actorId.trim()
    if (!id || !updatedBy) return

    await this.client.postJson<unknown>(`/api/v1/orders/${encodeURIComponent(id)}/attribute-persisted-snapshot`, {
      updatedBy,
    })
  }

  async updateOrder(orderId: string, patch: OrderUpdateInput): Promise<OrderRow> {
    const id = orderId.trim()
    return await this.client.patchJson<OrderRow>(`/api/v1/orders/${encodeURIComponent(id)}`, patch)
  }

  async resolveOriginalIdByOrderId(orderId: string): Promise<string | null> {
    const id = orderId.trim()
    if (!id) return null

    try {
      const response = await this.client.getJson<{ original_id: string | null }>(
        `/api/v1/orders/${encodeURIComponent(id)}/resolve-original-id`
      )

      if (response.original_id && response.original_id.trim()) {
        return response.original_id
      }
    } catch (error) {
      this.logger.warn('HttpOrderReadService', 'resolveOriginalIdByOrderId via API failed', {
        orderId: id,
        error,
      })
    }

    return await this.fallback.resolveOriginalIdByOrderId(id)
  }

  async listActiveItems(orderId: string): Promise<OrderItemRow[]> {
    return await this.fallback.listActiveItems(orderId)
  }

  async listActiveItemsByOriginalId(originalId: string): Promise<OrderItemRow[]> {
    return await this.fallback.listActiveItemsByOriginalId(originalId)
  }

  async findItemHistoryByOriginalId(originalId: string): Promise<OrderItemRow[]> {
    return await this.fallback.findItemHistoryByOriginalId(originalId)
  }

  async createItem(input: OrderItemCreateInput): Promise<OrderItemRow> {
    return await this.fallback.createItem(input)
  }

  async updateItem(itemId: string, patch: OrderItemUpdateInput): Promise<OrderItemRow> {
    return await this.fallback.updateItem(itemId, patch)
  }

  async deleteItem(itemId: string): Promise<void> {
    await this.fallback.deleteItem(itemId)
  }

  async getPdfPreviewSrc(storagePath: string): Promise<StoragePreview | null> {
    const trimmed = storagePath.trim()
    if (!trimmed) return null

    try {
      const requestPath = withQuery(
        '/api/v1/storage/preview',
        new URLSearchParams({ storage_path: trimmed }).toString()
      )
      const response = await this.client.getJson<StoragePreviewResponse>(requestPath)

      const src =
        response.signed_url ??
        response.signedUrl ??
        response.preview_url ??
        response.previewUrl ??
        response.url ??
        response.src ??
        null

      if (src && src.trim()) {
        return { src }
      }
    } catch (error) {
      this.logger.warn('HttpOrderReadService', 'getPdfPreviewSrc via API failed', {
        storagePath: trimmed,
        error,
      })
    }

    return await this.fallback.getPdfPreviewSrc(trimmed)
  }
}
