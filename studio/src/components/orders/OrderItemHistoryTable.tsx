import { formatDateTimeShort } from '../../lib/utils/date'
import { formatDecimal } from '../../lib/utils/number'
import type { OrderItemRow } from '../../services/core/order/types'

function formatActor(updatedBy: string | null, currentUserId: string, t: (key: string) => string): string {
  if (!updatedBy) return t('order.detail.audit.system')
  if (updatedBy === currentUserId) return t('order.detail.audit.you')
  return `${updatedBy.slice(0, 8)}…`
}

function formatValue(value: string | number | null | undefined, language: string): string {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'number') return formatDecimal(value, language, { maximumFractionDigits: 6 })
  return value.trim() ? value : '-'
}

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
    const prev = formatValue(prevValue, language)
    const next = formatValue(nextValue, language)
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
    <div>
      {history.length === 0 ? (
        <div className="text-sm text-[color:var(--text-secondary)]">{t('order.detail.historyEmpty')}</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="text-left">
              <tr className="table-divider-strong">
                <th className="py-2 pr-4 whitespace-nowrap w-[11.5rem]">{t('order.detail.audit.when')}</th>
                <th className="py-2 pr-4 whitespace-nowrap w-[6.5rem]">{t('order.detail.audit.by')}</th>
                <th className="py-2 w-full">{t('order.detail.audit.changes')}</th>
              </tr>
            </thead>
            <tbody>
              {history.map((v, index) => (
                <tr key={v.id} className="table-divider">
                  <td className="py-2 pr-4 whitespace-nowrap">{formatDateTimeShort(v.created_at, language)}</td>
                  <td className="py-2 pr-4 whitespace-nowrap">{formatActor(v.updated_by, currentUserId, t)}</td>
                  <td className="py-2">{diffItemRows(v, history[index + 1] ?? null, t, language)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
