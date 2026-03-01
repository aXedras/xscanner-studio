import { formatDecimal } from '../../lib/utils/number'

export function formatHistoryActor(updatedBy: string | null, currentUserId: string, t: (key: string) => string): string {
  if (!updatedBy) return t('order.detail.audit.system')
  if (updatedBy === currentUserId) return t('order.detail.audit.you')
  return `${updatedBy.slice(0, 8)}…`
}

export function formatHistoryValue(value: string | number | null | undefined, language: string): string {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'number') return formatDecimal(value, language, { maximumFractionDigits: 6 })
  return value.trim() ? value : '-'
}
