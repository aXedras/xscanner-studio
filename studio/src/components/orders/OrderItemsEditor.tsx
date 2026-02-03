import { useMemo, useState } from 'react'
import type { OrderItemRow, OrderItemUpdateInput } from '../../services/core/order/types'
import { ActionIconButton } from '../ui/ActionIconButton'
import { DetailsIcon } from '../ui/ActionIcons'
import { OrderItemModal } from './OrderItemModal'

export type OrderItemsEditorProps = {
  t: (key: string) => string
  items: OrderItemRow[]
  editable: boolean
  disabled: boolean
  saving: boolean
  onPatchItem: (itemId: string, patch: OrderItemUpdateInput) => void
  loadItemHistory?: (originalId: string) => Promise<OrderItemRow[]>
  currentUserId: string
  language: string
}

function formatWeight(weight: string | null, weightUnit: OrderItemRow['weight_unit']): string {
  const trimmed = (weight ?? '').trim()
  if (!trimmed) return ''
  if (!weightUnit || weightUnit === 'unknown') return trimmed
  return `${trimmed} ${weightUnit}`
}

export function OrderItemsEditor(props: OrderItemsEditorProps) {
  const { t, items, editable, disabled, saving, onPatchItem, loadItemHistory, currentUserId, language } = props

  const isDisabled = disabled || saving

  const [selectedItemId, setSelectedItemId] = useState<string | null>(null)
  const selectedRow = useMemo(
    () => (selectedItemId ? (items.find(row => row.id === selectedItemId) ?? null) : null),
    [selectedItemId, items]
  )

  const openView = (row: OrderItemRow) => {
    setSelectedItemId(row.id)
  }

  const closeModal = () => {
    setSelectedItemId(null)
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-semibold">{t('order.detail.sections.orderItems')}</h4>
      </div>

      {items.length === 0 ? (
        <div className="text-sm text-[color:var(--text-secondary)]">{t('order.detail.items.empty')}</div>
      ) : (
        <div className="max-w-full overflow-x-hidden">
          <table className="w-full table-fixed text-sm">
            <thead>
              <tr className="text-left text-[color:var(--text-secondary)]">
                <th className="py-2 pr-3 w-[12rem] sm:w-[26%] whitespace-nowrap">
                  {t('order.detail.items.fields.item')}
                </th>
                <th className="hidden sm:table-cell py-2 pr-3 sm:w-[18%] whitespace-nowrap">
                  {t('order.detail.items.fields.serialNumber')}
                </th>
                <th className="hidden sm:table-cell py-2 pr-3 sm:w-[12%] whitespace-nowrap">
                  {t('order.detail.items.fields.quantity')}
                </th>
                <th className="hidden sm:table-cell py-2 pr-3 sm:w-[22%] whitespace-nowrap">
                  {t('order.detail.items.fields.producer')}
                </th>
                <th className="hidden sm:table-cell py-2 pr-3 sm:w-[14%] whitespace-nowrap">
                  {t('order.detail.items.fields.metal')}
                </th>
                <th className="hidden sm:table-cell py-2 pr-3 sm:w-[14%] whitespace-nowrap">
                  {t('order.detail.items.fields.weight')}
                </th>
                <th className="py-2 pr-0 w-[3.25rem] sm:w-[8%]" />
              </tr>
            </thead>
            <tbody>
              {items.map(row => (
                <tr key={row.id} className="border-t border-[color:var(--bg-card-border)] align-top">
                  <td className="py-2 pr-3">
                    <div className="py-2 truncate" title={row.item ?? ''}>
                      {row.item ?? '—'}
                    </div>

                    <div className="sm:hidden pb-2 text-xs text-[color:var(--text-secondary)] space-y-1">
                      <div className="flex gap-2 min-w-0">
                        <span className="shrink-0">{t('order.detail.items.fields.serialNumber')}:</span>
                        <span className="truncate text-[color:var(--text-primary)]">{row.serial_number ?? '—'}</span>
                      </div>
                      <div className="flex gap-2 min-w-0">
                        <span className="shrink-0">{t('order.detail.items.fields.quantity')}:</span>
                        <span className="truncate text-[color:var(--text-primary)]">{row.quantity ?? '—'}</span>
                      </div>
                      <div className="flex gap-2 min-w-0">
                        <span className="shrink-0">{t('order.detail.items.fields.producer')}:</span>
                        <span className="truncate text-[color:var(--text-primary)]">{row.producer ?? '—'}</span>
                      </div>
                      <div className="flex gap-2 min-w-0">
                        <span className="shrink-0">{t('order.detail.items.fields.metal')}:</span>
                        <span className="truncate text-[color:var(--text-primary)]">{row.metal}</span>
                      </div>
                      <div className="flex gap-2 min-w-0">
                        <span className="shrink-0">{t('order.detail.items.fields.weight')}:</span>
                        <span className="truncate text-[color:var(--text-primary)]">
                          {formatWeight(row.weight, row.weight_unit) || '—'}
                        </span>
                      </div>
                    </div>
                  </td>
                  <td className="hidden sm:table-cell py-2 pr-3">
                    <div className="py-2 truncate" title={row.serial_number ?? ''}>
                      {row.serial_number ?? '—'}
                    </div>
                  </td>
                  <td className="hidden sm:table-cell py-2 pr-3">
                    <div className="py-2 truncate" title={row.quantity ?? ''}>
                      {row.quantity ?? '—'}
                    </div>
                  </td>
                  <td className="hidden sm:table-cell py-2 pr-3">
                    <div className="py-2 truncate" title={row.producer ?? ''}>
                      {row.producer ?? '—'}
                    </div>
                  </td>
                  <td className="hidden sm:table-cell py-2 pr-3">
                    <div className="py-2 truncate" title={row.metal}>
                      {row.metal}
                    </div>
                  </td>
                  <td className="hidden sm:table-cell py-2 pr-3">
                    <div className="py-2 truncate" title={formatWeight(row.weight, row.weight_unit)}>
                      {formatWeight(row.weight, row.weight_unit) || '—'}
                    </div>
                  </td>

                  <td className="py-2 pr-0 align-middle">
                    <div className="flex justify-end gap-1 py-1">
                      <ActionIconButton
                        label={t('common.action.showDetails')}
                        onClick={() => openView(row)}
                        inactive={false}
                        className="text-[16px]"
                      >
                        <DetailsIcon />
                      </ActionIconButton>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <OrderItemModal
        t={t}
        row={selectedRow}
        editable={editable}
        disabled={isDisabled}
        onClose={closeModal}
        onSave={onPatchItem}
        loadHistory={loadItemHistory}
        currentUserId={currentUserId}
        language={language}
      />
    </div>
  )
}
