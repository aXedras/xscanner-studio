import { useEffect, useState } from 'react'
import type { OrderItemRow, OrderItemUpdateInput } from '../../services/core/order/types'
import { ORDER_ENUMS } from '../../services/core/order/types'
import { ActionIconButton } from '../ui/ActionIconButton'
import { EditIcon, RegisterIcon, RejectIcon } from '../ui/ActionIcons'
import { Modal } from '../ui/Modal'
import { OrderItemHistoryTable } from './OrderItemHistoryTable'
import { formatDecimalInput } from '../../lib/utils/number'

type ModalMode = 'view' | 'edit'

type Draft = {
  item: string
  producer: string
  metal: OrderItemRow['metal']
  weight: string
  weightUnit: OrderItemRow['weight_unit']
  fineness: string
  form: OrderItemRow['form']
  serialNumber: string
  description: string
  quantity: string
  itemPrice: string
  totalPrice: string
}

type Props = {
  t: (key: string) => string
  row: OrderItemRow | null
  editable: boolean
  disabled: boolean
  onClose: () => void
  onSave: (itemId: string, patch: OrderItemUpdateInput) => void
  loadHistory?: (originalId: string) => Promise<OrderItemRow[]>
  currentUserId: string
  language: string
}

function formatMoneyInput(value: number | null, language: string): string {
  return formatDecimalInput(value, language, { maximumFractionDigits: 6 })
}

function parseNullableNumber(value: string): number | null {
  const trimmed = value.trim()
  if (!trimmed) return null
  const normalized = trimmed.replace(',', '.')
  const parsed = Number(normalized)
  return Number.isFinite(parsed) ? parsed : null
}

export function OrderItemModal({
  t,
  row,
  editable,
  disabled,
  onClose,
  onSave,
  loadHistory,
  currentUserId,
  language,
}: Props) {
  const [mode, setMode] = useState<ModalMode>('view')
  const [historyRows, setHistoryRows] = useState<OrderItemRow[]>([])
  const [historyLoading, setHistoryLoading] = useState(false)

  const [draft, setDraft] = useState<Draft>({
    item: '',
    producer: '',
    metal: 'unknown',
    weight: '',
    weightUnit: 'unknown',
    fineness: '',
    form: 'unknown',
    serialNumber: '',
    description: '',
    quantity: '',
    itemPrice: '',
    totalPrice: '',
  })

  useEffect(() => {
    if (!row) return
    setMode('view')
    setHistoryRows([])
    setDraft({
      item: row.item ?? '',
      producer: row.producer ?? '',
      metal: row.metal,
      weight: row.weight ?? '',
      weightUnit: row.weight_unit,
      fineness: row.fineness ?? '',
      form: row.form,
      serialNumber: row.serial_number ?? '',
      description: row.description ?? '',
      quantity: row.quantity ?? '',
      itemPrice: formatMoneyInput(row.item_price, language),
      totalPrice: formatMoneyInput(row.total_price, language),
    })
  }, [row, language])

  useEffect(() => {
    let isMounted = true

    const run = async () => {
      if (!row || !loadHistory) return

      const originalId = row.original_id ?? row.id
      setHistoryLoading(true)
      try {
        const rows = await loadHistory(originalId)
        if (!isMounted) return
        setHistoryRows(rows)
      } finally {
        if (isMounted) setHistoryLoading(false)
      }
    }

    run()
    return () => {
      isMounted = false
    }
  }, [row, loadHistory])

  const isEditMode = mode === 'edit'
  const isFieldDisabled = disabled || !isEditMode

  const enterEditMode = () => {
    if (!editable || disabled) return
    setMode('edit')
  }

  const handleSave = () => {
    if (!row) return
    if (!isEditMode) return

    onSave(row.id, {
      item: draft.item,
      producer: draft.producer,
      metal: draft.metal,
      weight: draft.weight,
      weight_unit: draft.weightUnit,
      fineness: draft.fineness,
      form: draft.form,
      serial_number: draft.serialNumber,
      description: draft.description,
      quantity: draft.quantity,
      item_price: parseNullableNumber(draft.itemPrice),
      total_price: parseNullableNumber(draft.totalPrice),
    })

    onClose()
  }

  const headerActions = isEditMode ? (
    <>
      <ActionIconButton label={t('common.action.save')} onClick={handleSave} inactive={disabled || !row}>
        <RegisterIcon />
      </ActionIconButton>
      <ActionIconButton label={t('common.action.close')} onClick={onClose} inactive={false}>
        <RejectIcon />
      </ActionIconButton>
    </>
  ) : (
    <>
      <ActionIconButton
        label={t('common.action.edit')}
        onClick={enterEditMode}
        inactive={disabled || !editable || !row}
      >
        <EditIcon />
      </ActionIconButton>
      <ActionIconButton label={t('common.action.close')} onClick={onClose} inactive={false}>
        <RejectIcon />
      </ActionIconButton>
    </>
  )

  return (
    <Modal
      open={!!row}
      title={`${isEditMode ? t('common.action.edit') : t('common.action.showDetails')} · ${t('order.detail.sections.orderItems')}`}
      closeLabel={t('common.action.close')}
      headerActions={headerActions}
      hideCloseButton
      onClose={onClose}
      widthClassName="max-w-2xl"
    >
      <div className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <label className="block">
            <div className="text-label mb-1">{t('order.detail.items.fields.item')}</div>
            <input
              className="input w-full"
              value={draft.item}
              disabled={isFieldDisabled}
              onChange={e => setDraft(prev => ({ ...prev, item: e.target.value }))}
            />
          </label>

          <label className="block">
            <div className="text-label mb-1">{t('order.detail.items.fields.producer')}</div>
            <input
              className="input w-full"
              value={draft.producer}
              disabled={isFieldDisabled}
              onChange={e => setDraft(prev => ({ ...prev, producer: e.target.value }))}
            />
          </label>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <label className="block">
            <div className="text-label mb-1">{t('order.detail.items.fields.metal')}</div>
            <select
              className="input w-full"
              value={draft.metal}
              disabled={isFieldDisabled}
              onChange={e => setDraft(prev => ({ ...prev, metal: e.target.value as Draft['metal'] }))}
            >
              {ORDER_ENUMS.bullion_metal.map(value => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <div className="text-label mb-1">{t('order.detail.items.fields.form')}</div>
            <select
              className="input w-full"
              value={draft.form}
              disabled={isFieldDisabled}
              onChange={e => setDraft(prev => ({ ...prev, form: e.target.value as Draft['form'] }))}
            >
              {ORDER_ENUMS.bullion_form.map(value => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <label className="block">
            <div className="text-label mb-1">{t('order.detail.items.fields.weight')}</div>
            <input
              className="input w-full"
              value={draft.weight}
              disabled={isFieldDisabled}
              onChange={e => setDraft(prev => ({ ...prev, weight: e.target.value }))}
            />
          </label>

          <label className="block">
            <div className="text-label mb-1">{t('order.detail.items.fields.weightUnit')}</div>
            <select
              className="input w-full"
              value={draft.weightUnit}
              disabled={isFieldDisabled}
              onChange={e => setDraft(prev => ({ ...prev, weightUnit: e.target.value as Draft['weightUnit'] }))}
            >
              {ORDER_ENUMS.bullion_weight_unit.map(value => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <label className="block">
            <div className="text-label mb-1">{t('order.detail.items.fields.fineness')}</div>
            <input
              className="input w-full"
              value={draft.fineness}
              disabled={isFieldDisabled}
              onChange={e => setDraft(prev => ({ ...prev, fineness: e.target.value }))}
            />
          </label>

          <label className="block">
            <div className="text-label mb-1">{t('order.detail.items.fields.quantity')}</div>
            <input
              className="input w-full"
              value={draft.quantity}
              disabled={isFieldDisabled}
              onChange={e => setDraft(prev => ({ ...prev, quantity: e.target.value }))}
            />
          </label>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <label className="block md:col-span-2">
            <div className="text-label mb-1">{t('order.detail.items.fields.serialNumber')}</div>
            <input
              className="input w-full"
              value={draft.serialNumber}
              disabled={isFieldDisabled}
              onChange={e => setDraft(prev => ({ ...prev, serialNumber: e.target.value }))}
            />
          </label>
        </div>

        <label className="block">
          <div className="text-label mb-1">{t('order.detail.items.fields.description')}</div>
          <textarea
            className="input w-full min-h-[6rem]"
            value={draft.description}
            disabled={isFieldDisabled}
            onChange={e => setDraft(prev => ({ ...prev, description: e.target.value }))}
          />
        </label>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <label className="block">
            <div className="text-label mb-1">{t('order.detail.items.fields.itemPrice')}</div>
            <input
              className="input w-full"
              inputMode="decimal"
              value={draft.itemPrice}
              disabled={isFieldDisabled}
              onChange={e => setDraft(prev => ({ ...prev, itemPrice: e.target.value }))}
            />
          </label>

          <label className="block">
            <div className="text-label mb-1">{t('order.detail.items.fields.totalPrice')}</div>
            <input
              className="input w-full"
              inputMode="decimal"
              value={draft.totalPrice}
              disabled={isFieldDisabled}
              onChange={e => setDraft(prev => ({ ...prev, totalPrice: e.target.value }))}
            />
          </label>
        </div>

        {!isEditMode && row ? (
          <details className="rounded-md border border-[color:var(--bg-card-border)] bg-[color:var(--bg-card)]">
            <summary className="cursor-pointer select-none px-3 py-2 text-sm font-semibold">Raw</summary>
            <div className="px-3 pb-3">
              <pre className="text-xs overflow-auto whitespace-pre-wrap break-words max-h-[24vh]">
                {JSON.stringify(row.raw ?? {}, null, 2)}
              </pre>
            </div>
          </details>
        ) : null}

        {!isEditMode && row && loadHistory ? (
          <div className="rounded-md border border-[color:var(--bg-card-border)] bg-[color:var(--bg-card)] p-3">
            <div className="text-sm font-semibold mb-2">{t('order.detail.historyTitle')}</div>
            {historyLoading ? (
              <div className="text-sm text-[color:var(--text-secondary)]">{t('common.status.loading')}</div>
            ) : historyRows.length <= 1 ? (
              <div className="text-sm text-[color:var(--text-secondary)]">{t('order.detail.historyEmpty')}</div>
            ) : (
              <OrderItemHistoryTable history={historyRows} currentUserId={currentUserId} language={language} t={t} />
            )}
          </div>
        ) : null}
      </div>
    </Modal>
  )
}
