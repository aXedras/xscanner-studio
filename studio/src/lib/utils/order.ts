import type { TFunction } from 'i18next'

const ERROR_SHA256_PREFIX = 'error-sha256:'

function shortenHash(value: string, keep: number): string {
  const trimmed = value.trim()
  if (trimmed.length <= keep) return trimmed
  return `${trimmed.slice(0, keep)}…`
}

export function formatOrderDocumentNumberForDisplay(documentNumber: string | null | undefined, t: TFunction): string {
  const value = typeof documentNumber === 'string' ? documentNumber.trim() : ''
  if (!value) return '-'

  if (value.startsWith(ERROR_SHA256_PREFIX)) {
    const hash = value.slice(ERROR_SHA256_PREFIX.length)
    const hashShort = shortenHash(hash, 8)
    return t('order.fields.documentNumberErrorHash', { hash: hashShort })
  }

  return value
}
