import { formatCurrency, formatDecimal } from '../../lib/utils/number'
import type { OrderRow } from '../../services/core/order/types'
import { formatHistoryValue } from './historyTableFormatting'
import { AuditHistoryTable } from './historyTableShared'

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
    const prev = formatHistoryValue(prevValue, language)
    const next = formatHistoryValue(nextValue, language)
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
    <AuditHistoryTable
      history={history}
      currentUserId={currentUserId}
      language={language}
      t={t}
      title={t('order.detail.historyTitle')}
      getChanges={(current, previous) => diffOrderRows(current, previous, language, t)}
    />
  )
}
