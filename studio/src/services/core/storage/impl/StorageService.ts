import type { SupabaseClient } from '@supabase/supabase-js'
import type { ILogger } from '../../../../lib/utils/logging'
import type { IStorageService, StoragePreview } from '../IStorageService'

const DEFAULT_BUCKET = (import.meta.env.VITE_SUPABASE_STORAGE_BUCKET as string) || 'extractions'
const DEFAULT_EXPIRES_IN_SECONDS = 60 * 60

class StoragePreviewError extends Error {
  declare readonly status?: number
  declare readonly details?: string

  constructor(message: string, input: { status?: number; details?: string }) {
    super(message)
    this.name = 'StoragePreviewError'
    this.status = input.status
    this.details = input.details
  }
}

const toStatus = (error: unknown): number | undefined => {
  if (!error || typeof error !== 'object') return undefined
  const anyError = error as Record<string, unknown>
  const statusCode = anyError.statusCode
  const status = anyError.status

  if (typeof statusCode === 'number') return statusCode
  if (typeof statusCode === 'string') {
    const parsed = Number(statusCode)
    if (Number.isFinite(parsed)) return parsed
  }

  if (typeof status === 'number') return status
  if (typeof status === 'string') {
    const parsed = Number(status)
    if (Number.isFinite(parsed)) return parsed
  }

  return undefined
}

function normalizeStoragePath(input: { bucket: string; storagePath: string }): string {
  const { bucket, storagePath } = input
  const trimmed = storagePath.trim().replace(/^\/+/, '')

  // Handle already-prefixed keys like "extractions/<path>".
  if (trimmed.startsWith(`${bucket}/`)) {
    return trimmed.slice(bucket.length + 1)
  }

  // Handle full Supabase Storage URLs.
  if (/^https?:\/\//i.test(trimmed)) {
    try {
      const url = new URL(trimmed)
      const marker = `/${bucket}/`
      const idx = url.pathname.indexOf(marker)
      if (idx !== -1) {
        return url.pathname.slice(idx + marker.length)
      }
    } catch {
      // fallthrough
    }
  }

  return trimmed
}

export class StorageService implements IStorageService {
  declare private readonly supabase: SupabaseClient
  declare private readonly logger: ILogger

  constructor(supabase: SupabaseClient, logger: ILogger) {
    this.supabase = supabase
    this.logger = logger
  }

  async getImagePreviewSrc(
    storagePath: string,
    options?: {
      bucket?: string
      expiresInSeconds?: number
    }
  ): Promise<StoragePreview | null> {
    const bucket = options?.bucket ?? DEFAULT_BUCKET
    const expiresInSeconds = options?.expiresInSeconds ?? DEFAULT_EXPIRES_IN_SECONDS

    const normalizedPath = normalizeStoragePath({ bucket, storagePath })

    const signed = await this.supabase.storage.from(bucket).createSignedUrl(normalizedPath, expiresInSeconds)
    if (!signed.error && signed.data?.signedUrl) {
      return { src: signed.data.signedUrl }
    }

    if (signed.error) {
      this.logger.warn('StorageService', 'createSignedUrl failed', {
        bucket,
        storagePath,
        normalizedPath,
        error: signed.error,
      })
    }

    const download = await this.supabase.storage.from(bucket).download(normalizedPath)
    if (download.error) {
      this.logger.error('StorageService', 'storage.download failed', {
        bucket,
        storagePath,
        normalizedPath,
        error: download.error,
      })

      const status = toStatus(signed.error) ?? toStatus(download.error)
      const details = JSON.stringify(
        {
          bucket,
          storagePath,
          normalizedPath,
          signedUrlError: signed.error,
          downloadError: download.error,
        },
        null,
        2
      )

      throw new StoragePreviewError('Image preview unavailable', {
        status,
        details,
      })
    }

    const objectUrl = URL.createObjectURL(download.data)
    return {
      src: objectUrl,
      revoke: () => URL.revokeObjectURL(objectUrl),
    }
  }
}
