import { useMemo } from 'react'
import type { ReactNode } from 'react'
import type { OrderCanonicalFieldsForm } from './orderCanonicalFieldsForm'

type TwoColRowProps = {
  leftLabel: string
  rightLabel?: string
  leftField: ReactNode
  rightField?: ReactNode
}

function TwoColRow({ leftLabel, rightLabel, leftField, rightField }: TwoColRowProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-1">
      <div className="text-[11px] text-[color:var(--text-secondary)] truncate" title={leftLabel}>
        {leftLabel}
      </div>
      <div className="text-[11px] text-[color:var(--text-secondary)] truncate" title={rightLabel}>
        {rightLabel ?? ''}
      </div>

      <div className="min-w-0">{leftField}</div>
      <div className="min-w-0">{rightField ?? null}</div>
    </div>
  )
}

export type OrderCanonicalFieldsEditorProps = {
  t: (key: string) => string
  form: OrderCanonicalFieldsForm
  disabled: boolean
  saving: boolean
  onChange: (next: OrderCanonicalFieldsForm) => void
}

export function OrderCanonicalFieldsEditor(props: OrderCanonicalFieldsEditorProps) {
  const { t, form, disabled, saving, onChange } = props

  const isDisabled = disabled || saving

  const sections = useMemo(
    () => [
      {
        title: t('order.detail.sections.parties'),
        fields: (
          <div className="space-y-3">
            <TwoColRow
              leftLabel={t('order.detail.fields.sellerName')}
              rightLabel={t('order.detail.fields.buyerName')}
              leftField={
                <input
                  className="input w-full"
                  value={form.sellerName}
                  disabled={isDisabled}
                  onChange={e => onChange({ ...form, sellerName: e.target.value })}
                />
              }
              rightField={
                <input
                  className="input w-full"
                  value={form.buyerName}
                  disabled={isDisabled}
                  onChange={e => onChange({ ...form, buyerName: e.target.value })}
                />
              }
            />
          </div>
        ),
      },
      {
        title: t('order.detail.sections.orderTerms'),
        fields: (
          <div className="space-y-3">
            <TwoColRow
              leftLabel={t('order.fields.orderNumber')}
              rightLabel={t('order.detail.fields.transactionType')}
              leftField={
                <input
                  className="input w-full"
                  value={form.orderNumber}
                  disabled={isDisabled}
                  onChange={e => onChange({ ...form, orderNumber: e.target.value })}
                />
              }
              rightField={
                <input
                  className="input w-full"
                  value={form.transactionType}
                  disabled={isDisabled}
                  onChange={e => onChange({ ...form, transactionType: e.target.value })}
                />
              }
            />

            <TwoColRow
              leftLabel={t('order.detail.fields.orderDate')}
              rightLabel={t('order.detail.fields.valueDate')}
              leftField={
                <input
                  className="input w-full"
                  type="date"
                  value={form.orderDate}
                  disabled={isDisabled}
                  onChange={e => onChange({ ...form, orderDate: e.target.value })}
                />
              }
              rightField={
                <input
                  className="input w-full"
                  type="date"
                  value={form.valueDate}
                  disabled={isDisabled}
                  onChange={e => onChange({ ...form, valueDate: e.target.value })}
                />
              }
            />

            <TwoColRow
              leftLabel={t('order.detail.fields.shippingDate')}
              rightLabel={t('order.detail.fields.currency')}
              leftField={
                <input
                  className="input w-full"
                  type="date"
                  value={form.shippingDate}
                  disabled={isDisabled}
                  onChange={e => onChange({ ...form, shippingDate: e.target.value })}
                />
              }
              rightField={
                <input
                  className="input w-full"
                  value={form.currency}
                  disabled={isDisabled}
                  onChange={e => onChange({ ...form, currency: e.target.value })}
                />
              }
            />

            <TwoColRow
              leftLabel={t('order.detail.fields.subtotalAmount')}
              rightLabel={t('order.detail.fields.shippingChargesAmount')}
              leftField={
                <input
                  className="input w-full"
                  inputMode="decimal"
                  value={form.subtotalAmount}
                  disabled={isDisabled}
                  onChange={e => onChange({ ...form, subtotalAmount: e.target.value })}
                />
              }
              rightField={
                <input
                  className="input w-full"
                  inputMode="decimal"
                  value={form.shippingChargesAmount}
                  disabled={isDisabled}
                  onChange={e => onChange({ ...form, shippingChargesAmount: e.target.value })}
                />
              }
            />

            <TwoColRow
              leftLabel={t('order.detail.fields.otherChargesAmount')}
              rightLabel={t('order.detail.fields.totalAmount')}
              leftField={
                <input
                  className="input w-full"
                  inputMode="decimal"
                  value={form.otherChargesAmount}
                  disabled={isDisabled}
                  onChange={e => onChange({ ...form, otherChargesAmount: e.target.value })}
                />
              }
              rightField={
                <input
                  className="input w-full"
                  inputMode="decimal"
                  value={form.totalAmount}
                  disabled={isDisabled}
                  onChange={e => onChange({ ...form, totalAmount: e.target.value })}
                />
              }
            />
          </div>
        ),
      },
    ],
    [form, isDisabled, onChange, t]
  )

  return (
    <div className="space-y-6">
      {sections.map(section => (
        <section key={section.title}>
          <h4 className="text-sm font-semibold mb-3">{section.title}</h4>
          {section.fields}
        </section>
      ))}
    </div>
  )
}
