import { useState } from 'react'
import type { TFunction } from 'i18next'

import type { OrderItemRow, OrderRow } from '../../services/core/order/types'
import { formatIsoDateShort } from '../../lib/utils/date'
import { formatOrderDocumentNumberForDisplay } from '../../lib/utils/order'
import { OrderCanonicalFieldsEditor } from './OrderCanonicalFieldsEditor'
import { OrderCanonicalFieldsView } from './OrderCanonicalFieldsView'
import type { OrderCanonicalFieldsForm } from './orderCanonicalFieldsForm'
import { OrderItemsEditor } from './OrderItemsEditor'
import { ActionIconButton } from '../ui/ActionIconButton'
import { BugIcon, DeleteIcon, DownloadIcon, EditIcon, RegisterIcon, RejectIcon } from '../ui/ActionIcons'
import { OrderStatusBadge } from './OrderStatusBadge'
import { OrderDocumentTypeBadge } from './OrderDocumentTypeBadge'
import { OrderHistoryTable } from './OrderHistoryTable'
import { OrderDebugModal } from './OrderDebugModal'
import { ConfidenceBadge } from '../extractions/ConfidenceBadge'

type Props = {
  t: TFunction
  language: string
  order: OrderRow
  history: OrderRow[]
  items: OrderItemRow[]
  currentUserId: string

  pdfSrc: string | null

  isEditing: boolean
  saving: boolean
  canEdit: boolean
  canSave: boolean
  canDelete: boolean

  form: OrderCanonicalFieldsForm | null
  onFormChange: (next: OrderCanonicalFieldsForm) => void

  onStartEdit: () => void
  onCancelEdit: () => void
  onSave: () => void
  onDelete: () => void

  onPatchItem: (itemId: string, patch: Partial<OrderItemRow>) => Promise<void>
  loadItemHistory?: (originalId: string) => Promise<OrderItemRow[]>

  finalPretty: string
  metaPretty: string
  rawSignalsPretty: string
  markerText: string
  rawText: string
  pdfText?: string
  tracePretty: string
}

export function OrderDetailView({
  t,
  language,
  order,
  history,
  items,
  currentUserId,
  pdfSrc,
  isEditing,
  saving,
  canEdit,
  canSave,
  canDelete,
  form,
  onFormChange,
  onStartEdit,
  onCancelEdit,
  onSave,
  onDelete,
  onPatchItem,
  loadItemHistory,
  finalPretty,
  metaPretty,
  rawSignalsPretty,
  markerText,
  rawText,
  pdfText,
  tracePretty,
}: Props) {
  const [debugOpen, setDebugOpen] = useState(false)

  const isPdfSrc = (src: string | null): boolean => {
    if (!src) return false
    const lower = src.toLowerCase()
    if (lower.includes('#zoom=')) return true
    if (lower.includes('.pdf')) return true
    if (lower.includes('content-type=application/pdf')) return true
    if (lower.includes('application/pdf')) return true
    return false
  }

  const showPdf = isPdfSrc(pdfSrc)
  const withPdfViewerParams = (src: string | null): string | null => {
    if (!src) return null
    if (src.includes('#')) return src

    // Chrome's built-in PDF viewer supports `#zoom=page-width`.
    // For other viewers, this is typically ignored (but harmless).
    return `${src}#zoom=page-width`
  }

  const pdfFrameSrc = withPdfViewerParams(pdfSrc)

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 min-w-0">
      <div className="panel min-w-0 overflow-hidden">
        {pdfSrc ? (
          <div>
            <div className="flex justify-end mb-2">
              <a
                className="btn btn-outline btn-icon btn-sm text-[18px]"
                href={pdfSrc}
                target="_blank"
                rel="noreferrer"
                aria-label={t('common.action.download')}
                title={t('common.action.download')}
              >
                <DownloadIcon />
              </a>
            </div>

            <div className="relative w-full overflow-hidden rounded-md h-[70vh] max-h-[820px] min-h-[420px]">
              {showPdf ? (
                <iframe
                  title="order-document"
                  src={pdfFrameSrc ?? undefined}
                  className="block w-full h-full"
                  style={{ border: 0 }}
                />
              ) : (
                <img
                  src={pdfSrc}
                  alt={t('order.detail.pdfTitle')}
                  className="block w-full h-full object-contain bg-black/5"
                />
              )}
            </div>
          </div>
        ) : (
          <div className="text-sm text-[color:var(--text-secondary)]">{t('order.detail.pdfUnavailable')}</div>
        )}
      </div>

      <div className="panel min-w-0">
        <div className="flex items-start justify-between gap-4 mb-3">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <OrderDocumentTypeBadge documentType={order.document_type} t={t} />
              <OrderStatusBadge status={order.status} t={t} />
              <ConfidenceBadge confidence={order.confidence} empty={null} />
            </div>

            <div className="mt-2 text-xs text-[color:var(--text-secondary)]">
              {t('common.fields.id')}: <span className="text-[color:var(--text-primary)]">{order.id}</span>
            </div>

            <div className="mt-3 grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="min-w-0">
                <div className="text-xs text-[color:var(--text-secondary)]">{t('order.fields.documentIssuer')}</div>
                <div className="text-sm break-words">{order.document_issuer}</div>
              </div>
              <div className="min-w-0">
                <div className="text-xs text-[color:var(--text-secondary)]">{t('order.fields.documentNumber')}</div>
                <div className="text-sm break-words">
                  {formatOrderDocumentNumberForDisplay(order.document_number, t)}
                </div>
              </div>
              <div className="min-w-0">
                <div className="text-xs text-[color:var(--text-secondary)]">{t('order.fields.documentDate')}</div>
                <div className="text-sm whitespace-nowrap">{formatIsoDateShort(order.document_date, language)}</div>
              </div>
            </div>
          </div>

          {!isEditing ? (
            <div className="flex items-center gap-2">
              <ActionIconButton label={t('common.action.edit')} onClick={onStartEdit} inactive={!canEdit}>
                <EditIcon />
              </ActionIconButton>
              <ActionIconButton label={t('common.action.delete')} onClick={onDelete} inactive={!canDelete}>
                <DeleteIcon />
              </ActionIconButton>
              <ActionIconButton
                label={t('order.detail.debugOpen')}
                onClick={() => setDebugOpen(true)}
                inactive={saving}
              >
                <BugIcon />
              </ActionIconButton>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <ActionIconButton label={t('common.action.save')} onClick={onSave} inactive={!canSave}>
                <RegisterIcon />
              </ActionIconButton>
              <ActionIconButton label={t('common.action.cancel')} onClick={onCancelEdit} inactive={saving}>
                <RejectIcon />
              </ActionIconButton>
              <ActionIconButton
                label={t('order.detail.debugOpen')}
                onClick={() => setDebugOpen(true)}
                inactive={saving}
              >
                <BugIcon />
              </ActionIconButton>
            </div>
          )}
        </div>

        {!isEditing ? (
          <div className="space-y-6">
            <OrderCanonicalFieldsView t={t} language={language} order={order} />
            <OrderItemsEditor
              t={t}
              items={items}
              editable={canEdit}
              disabled={!canEdit}
              saving={saving}
              onPatchItem={onPatchItem}
              loadItemHistory={loadItemHistory}
              currentUserId={currentUserId}
              language={language}
            />
          </div>
        ) : form ? (
          <div className="space-y-6">
            <OrderCanonicalFieldsEditor t={t} form={form} disabled={!order} saving={saving} onChange={onFormChange} />
            <OrderItemsEditor
              t={t}
              items={items}
              editable={canEdit}
              disabled={!canEdit}
              saving={saving}
              onPatchItem={onPatchItem}
              currentUserId={currentUserId}
              language={language}
            />
          </div>
        ) : null}
      </div>

      <div className="panel lg:col-span-2">
        <OrderHistoryTable history={history} currentUserId={currentUserId} language={language} t={t} />
      </div>

      <OrderDebugModal
        open={debugOpen}
        onClose={() => setDebugOpen(false)}
        t={t}
        language={language}
        finalPretty={finalPretty}
        metaPretty={metaPretty}
        rawSignalsPretty={rawSignalsPretty}
        markerText={markerText}
        rawText={rawText}
        pdfText={pdfText ?? ''}
        tracePretty={tracePretty}
      />
    </div>
  )
}
