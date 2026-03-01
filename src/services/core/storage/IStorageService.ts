export type StoragePreview = {
  src: string
  revoke?: () => void
}

export interface IStorageService {
  /**
   * Returns an image preview source URL for a given Storage key/path.
   * Prefers signed URLs and falls back to authenticated downloads (blob URL).
   */
  getImagePreviewSrc(
    storagePath: string,
    options?: {
      bucket?: string
      expiresInSeconds?: number
    }
  ): Promise<StoragePreview | null>

  /**
   * Returns a preview source URL for any stored file (e.g. PDFs).
   * Prefers signed URLs and falls back to authenticated downloads (blob URL).
   */
  getFilePreviewSrc(
    storagePath: string,
    options?: {
      bucket?: string
      expiresInSeconds?: number
    }
  ): Promise<StoragePreview | null>
}
