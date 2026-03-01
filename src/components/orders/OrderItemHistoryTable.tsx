import type { OrderItemRow } from '../../services/core/order/types'
import { formatHistoryValue } from './historyTableFormatting'
import { AuditHistoryTable } from './historyTableShared'

function formatWeight(weight: string | null, unit: OrderItemRow['weight_unit']): string {
  const trimmed = (weight ?? '').trim()
  if (!trimmed) return '-'
  if (!unit || unit === 'unknown') return trimmed
  return `${trimmed} ${unit}`
}

function diffItemRows(
  current: OrderItemRow,
  previous: OrderItemRow | null,
  t: (key: string) => string,
  language: string
): string {
  if (!previous) return '—'

  const changes: string[] = []
  const push = (
    label: string,
    prevValue: string | number | null | undefined,
    nextValue: string | number | null | undefined
  ) => {
    const prev = formatHistoryValue(prevValue, language)
    const next = formatHistoryValue(nextValue, language)
    if (prev !== next) changes.push(`${label}: ${prev} → ${next}`)
  }

  push(t('order.detail.items.fields.item'), previous.item, current.item)
  push(t('order.detail.items.fields.producer'), previous.producer, current.producer)
  push(t('order.detail.items.fields.metal'), previous.metal, current.metal)
  push(t('order.detail.items.fields.form'), previous.form, current.form)

  const prevWeight = formatWeight(previous.weight, previous.weight_unit)
  const nextWeight = formatWeight(current.weight, current.weight_unit)
  if (prevWeight !== nextWeight) changes.push(`${t('order.detail.items.fields.weight')}: ${prevWeight} → ${nextWeight}`)

  push(t('order.detail.items.fields.fineness'), previous.fineness, current.fineness)
  push(t('order.detail.items.fields.quantity'), previous.quantity, current.quantity)

  push(t('order.detail.items.fields.serialNumber'), previous.serial_number, current.serial_number)

  push(t('order.detail.items.fields.description'), previous.description, current.description)
  push(t('order.detail.items.fields.itemPrice'), previous.item_price, current.item_price)
  push(t('order.detail.items.fields.totalPrice'), previous.total_price, current.total_price)

  if (changes.length === 0) return '—'
  return changes.join(' · ')
}

export type OrderItemHistoryTableProps = {
  history: OrderItemRow[]
  currentUserId: string
  language: string
  t: (key: string) => string
}

export function OrderItemHistoryTable(props: OrderItemHistoryTableProps) {
  const { history, currentUserId, language, t } = props

  return (
    <AuditHistoryTable
      history={history}
      currentUserId={currentUserId}
      language={language}
      t={t}
      getChanges={(current, previous) => diffItemRows(current, previous, t, language)}
    />
  )
}
