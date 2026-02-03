import type { OrderRow } from '../../services/core/order/types'
import { formatIsoDateShort } from '../../lib/utils/date'
import { formatCurrency, formatDecimal } from '../../lib/utils/number'

type TwoColRowProps = {
  leftLabel: string
  rightLabel?: string
  leftValue: string
  rightValue?: string
}

function toDisplayValue(value: string): string {
  return value ? value : '—'
}

function TwoColRow({ leftLabel, rightLabel, leftValue, rightValue }: TwoColRowProps) {
  const left = toDisplayValue(leftValue)
  const right = rightLabel ? toDisplayValue(rightValue ?? '') : ''

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-1">
      <div className="text-[11px] text-[color:var(--text-secondary)] truncate" title={leftLabel}>
        {leftLabel}
      </div>
      <div className="text-[11px] text-[color:var(--text-secondary)] truncate" title={rightLabel}>
        {rightLabel ?? ''}
      </div>

      <div className="text-sm font-medium min-w-0 truncate" title={left}>
        {left}
      </div>
      <div className="text-sm font-medium min-w-0 truncate" title={right}>
        {right}
      </div>
    </div>
  )
}

type Props = {
  t: (key: string) => string
  language: string
  order: OrderRow
}

export function OrderCanonicalFieldsView({ t, language, order }: Props) {
  const currency = (order.currency ?? '').trim() || null

  const formatAmount = (amount: number | null | undefined): string => {
    if (amount === null || amount === undefined) return ''
    if (currency) return formatCurrency(amount, language, currency)
    return formatDecimal(amount, language, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  }

  return (
    <div className="space-y-6">
      <section>
        <h4 className="text-sm font-semibold mb-2">{t('order.detail.sections.parties')}</h4>
        <div className="space-y-3">
          <TwoColRow
            leftLabel={t('order.detail.fields.sellerName')}
            leftValue={order.seller_name ?? ''}
            rightLabel={t('order.detail.fields.buyerName')}
            rightValue={order.buyer_name ?? ''}
          />
        </div>
      </section>

      <section>
        <h4 className="text-sm font-semibold mb-2">{t('order.detail.sections.orderTerms')}</h4>
        <div className="space-y-3">
          <TwoColRow
            leftLabel={t('order.fields.orderNumber')}
            leftValue={order.order_number ?? ''}
            rightLabel={t('order.detail.fields.transactionType')}
            rightValue={order.transaction_type ?? ''}
          />
          <TwoColRow
            leftLabel={t('order.detail.fields.orderDate')}
            leftValue={order.order_date ? formatIsoDateShort(order.order_date, language) : ''}
            rightLabel={t('order.detail.fields.valueDate')}
            rightValue={order.value_date ? formatIsoDateShort(order.value_date, language) : ''}
          />
          <TwoColRow
            leftLabel={t('order.detail.fields.shippingDate')}
            leftValue={order.shipping_date ? formatIsoDateShort(order.shipping_date, language) : ''}
          />
          <TwoColRow
            leftLabel={t('order.detail.fields.currency')}
            leftValue={order.currency ?? ''}
            rightLabel={t('order.detail.fields.subtotalAmount')}
            rightValue={formatAmount(order.subtotal_amount)}
          />
          <TwoColRow
            leftLabel={t('order.detail.fields.shippingChargesAmount')}
            leftValue={formatAmount(order.shipping_charges_amount)}
            rightLabel={t('order.detail.fields.otherChargesAmount')}
            rightValue={formatAmount(order.other_charges_amount)}
          />
          <TwoColRow leftLabel={t('order.detail.fields.totalAmount')} leftValue={formatAmount(order.total_amount)} />
        </div>
      </section>
    </div>
  )
}
