import { formatDateTimeShort } from '../../lib/utils/date'
import { formatCurrency, formatDecimal } from '../../lib/utils/number'
import type { OrderRow } from '../../services/core/order/types'

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

function formatAmount(value: number | null | undefined, currency: string | null | undefined, language: string): string {
  if (value === null || value === undefined) return '-'
  const trimmedCurrency = (currency ?? '').trim()
  if (trimmedCurrency) return formatCurrency(value, language, trimmedCurrency)
  return formatDecimal(value, language, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function diffOrderRows(
  current: OrderRow,
  previous: OrderRow | null,
  language: string,
  t: (key: string) => string
): string {
  if (!previous) return t('order.detail.audit.initialUpload')

  const changes: string[] = []

  const safeJson = (value: unknown): string => {
    try {
      return JSON.stringify(value ?? null)
    } catch {
      return '[unserializable]'
    }
  }

  if ((previous.storage_path ?? '') !== (current.storage_path ?? '')) {
    changes.push(t('order.detail.audit.pdfReupload'))
  }

  const extractionSignalsChanged =
    (previous.processing_time ?? null) !== (current.processing_time ?? null) ||
    (previous.confidence ?? null) !== (current.confidence ?? null) ||
    (previous.strategy_used ?? '') !== (current.strategy_used ?? '')

  const extractedDataChanged = safeJson(previous.extracted_data) !== safeJson(current.extracted_data)

  if (extractionSignalsChanged || extractedDataChanged) {
    changes.push(t('order.detail.audit.extractionRerun'))
  }

  const push = (
    label: string,
    prevValue: string | number | null | undefined,
    nextValue: string | number | null | undefined
  ) => {
    const prev = formatValue(prevValue, language)
    const next = formatValue(nextValue, language)
    if (prev !== next) changes.push(`${label}: ${prev} → ${next}`)
  }

  push(t('order.fields.status'), previous.status, current.status)

  push(t('order.detail.fields.sellerName'), previous.seller_name, current.seller_name)
  push(t('order.detail.fields.buyerName'), previous.buyer_name, current.buyer_name)
  push(t('order.detail.fields.transactionType'), previous.transaction_type, current.transaction_type)

  push(t('order.fields.orderNumber'), previous.order_number, current.order_number)
  push(t('order.detail.fields.orderDate'), previous.order_date, current.order_date)
  push(t('order.detail.fields.valueDate'), previous.value_date, current.value_date)
  push(t('order.detail.fields.shippingDate'), previous.shipping_date, current.shipping_date)

  push(t('order.detail.fields.currency'), previous.currency, current.currency)
  push(
    t('order.detail.fields.subtotalAmount'),
    formatAmount(previous.subtotal_amount, previous.currency, language),
    formatAmount(current.subtotal_amount, current.currency, language)
  )
  push(
    t('order.detail.fields.shippingChargesAmount'),
    formatAmount(previous.shipping_charges_amount, previous.currency, language),
    formatAmount(current.shipping_charges_amount, current.currency, language)
  )
  push(
    t('order.detail.fields.otherChargesAmount'),
    formatAmount(previous.other_charges_amount, previous.currency, language),
    formatAmount(current.other_charges_amount, current.currency, language)
  )
  push(
    t('order.detail.fields.totalAmount'),
    formatAmount(previous.total_amount, previous.currency, language),
    formatAmount(current.total_amount, current.currency, language)
  )

  push(t('order.fields.strategyUsed'), previous.strategy_used, current.strategy_used)

  const prevError = previous.error ? previous.error : null
  const nextError = current.error ? current.error : null
  push(t('common.fields.error'), prevError, nextError)

  if (changes.length === 0) return '—'
  return changes.join(' · ')
}

export type OrderHistoryTableProps = {
  history: OrderRow[]
  currentUserId: string
  language: string
  t: (key: string) => string
}

export function OrderHistoryTable(props: OrderHistoryTableProps) {
  const { history, currentUserId, language, t } = props

  return (
    <div>
      <h3 className="text-body font-bold mb-3">{t('order.detail.historyTitle')}</h3>
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
                  <td className="py-2">{diffOrderRows(v, history[index + 1] ?? null, language, t)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
