import { useCallback, useRef, useState } from 'react'
import { services } from '../../services'
import { useAppTranslation, I18N_SCOPES } from '../../lib/i18n'
import { InlineSpinner } from '../ui/InlineSpinner'
import { ToggleSwitch } from '../ui/ToggleSwitch'
import { useUiMessages } from '../../ui/messages/UiMessagesContext'
import { createErrorMessage } from '../../ui/messages/fromError'
import type { OrderExtractResponse, OrderStrategyChoice } from '../../services/core/order/types'

export type UploadAndExtractOrderPanelProps = {
  initialStrategy?: OrderStrategyChoice
  initialUseDebugEndpoint?: boolean
  initialUseMockData?: boolean
  actorId?: string
  onResult?: (payload: { files: File[]; result: OrderExtractResponse }) => void
}

type UploadMode = 'pdf' | 'images'

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function extractReconciliationReady(meta: unknown): boolean | null {
  if (!isPlainObject(meta)) return null
  const readiness = meta.readiness
  if (!isPlainObject(readiness)) return null
  const ready = readiness.reconciliation_ready
  return typeof ready === 'boolean' ? ready : null
}

function extractReadinessReason(meta: unknown): string | null {
  if (!isPlainObject(meta)) return null
  const readiness = meta.readiness
  if (!isPlainObject(readiness)) return null
  const reason = readiness.reason
  return typeof reason === 'string' && reason.trim() ? reason : null
}

function extractPersistenceSkippedReasonCode(meta: unknown): string | null {
  if (!isPlainObject(meta)) return null
  const warningsAny = meta.warnings
  if (!Array.isArray(warningsAny)) return null

  for (const w of warningsAny) {
    if (typeof w !== 'string') continue
    if (w.startsWith('persistence_skipped_reason=')) {
      const code = w.slice('persistence_skipped_reason='.length).trim()
      return code ? code : null
    }
  }

  return null
}

function extractWarnings(meta: unknown): string[] {
  if (!isPlainObject(meta)) return []
  const warningsAny = meta.warnings
  if (!Array.isArray(warningsAny)) return []

  const warnings: string[] = []
  for (const w of warningsAny) {
    if (typeof w !== 'string') continue
    const trimmed = w.trim()
    if (!trimmed) continue
    warnings.push(trimmed)
  }
  return warnings
}

function isPdfFile(file: File): boolean {
  return String(file.type || '').toLowerCase() === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
}

function isImageFile(file: File): boolean {
  const type = String(file.type || '').toLowerCase()
  if (type.startsWith('image/')) return true
  const name = file.name.toLowerCase()
  return name.endsWith('.png') || name.endsWith('.jpg') || name.endsWith('.jpeg') || name.endsWith('.webp')
}

export function UploadAndExtractOrderPanel(props: UploadAndExtractOrderPanelProps) {
  const { t } = useAppTranslation(I18N_SCOPES.order)
  const { push } = useUiMessages()

  const { onResult } = props
  const actorId = String(props.actorId ?? '').trim() || undefined

  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const [processing, setProcessing] = useState(false)
  const [uploadMode, setUploadMode] = useState<UploadMode>('pdf')
  const [strategy, setStrategy] = useState<OrderStrategyChoice>(props.initialStrategy ?? 'auto')
  const [useDebugEndpoint, setUseDebugEndpoint] = useState(props.initialUseDebugEndpoint ?? false)
  const [useMockData, setUseMockData] = useState(props.initialUseMockData ?? false)

  const isBusy = processing

  const onPickFile = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const onFileSelected = useCallback(
    async (files: File[]) => {
      if (!files || files.length === 0) return

      if (uploadMode === 'pdf') {
        const file = files[0]
        if (!file || !isPdfFile(file)) {
          push(createErrorMessage(t, new Error('Bitte wähle eine PDF-Datei aus.')))
          return
        }
      } else {
        const invalid = files.find(f => !isImageFile(f))
        if (invalid) {
          push(createErrorMessage(t, new Error('Bitte wähle nur Bild-Dateien aus (png/jpg/webp).')))
          return
        }
      }

      setProcessing(true)
      try {
        const result = useDebugEndpoint
          ? await services.orderService.extractFromUploadDebug({ files, strategy, useMock: useMockData })
          : await services.orderService.extractFromUpload({ files, strategy, useMock: useMockData })

        const metaAny = isPlainObject(result.result) ? (result.result as Record<string, unknown>).meta : undefined

        const reconciliationReady = extractReconciliationReady(metaAny)
        const readinessReason = extractReadinessReason(metaAny)
        const hasPersistedOrder = Boolean(result.order_id)

        // If persistence succeeded we want to navigate to the order detail page
        // even if extraction was not fully successful (processing/parsing errors).
        if (hasPersistedOrder) {
          if (actorId && result.order_id) {
            try {
              await services.orderService.attributePersistedSnapshot(result.order_id, actorId)
            } catch (error) {
              // Attribution should not block the main extraction flow.
              // If this fails (e.g. due to RLS), history will show "System".
              services.logger.error('UploadAndExtractOrderPanel', 'actor attribution failed', error)
              push({
                variant: 'warning',
                title: t('common.toast.actorAttributionFailed.title'),
                description: t('common.toast.actorAttributionFailed.description'),
              })
            }
          }

          onResult?.({ files, result })

          // Simple rule: success confirmations are overlay toasts.
          // Any warnings/processing issues are shown as a sticky panel on the detail page.
          push({
            variant: 'success',
            title: t('common.toast.upload.title'),
            description: t('common.toast.upload.description'),
          })

          return
        }

        if (!result.success) {
          // Not persisted: show error as before.
          throw new Error(result.error || 'Order extraction failed')
        }

        if (!hasPersistedOrder) {
          const code = extractPersistenceSkippedReasonCode(metaAny)
          const reason =
            code === 'persistence_disabled'
              ? t('common.toast.uploadNotPersisted.reasons.persistenceDisabled')
              : code === 'unknown_document_issuer'
                ? t('common.toast.uploadNotPersisted.reasons.unknownIssuer')
                : t('common.toast.uploadNotPersisted.reasons.unknown')

          push({
            variant: 'warning',
            title: t('common.toast.uploadNotPersisted.title'),
            description: t('common.toast.uploadNotPersisted.description', { reason }),
          })
          return
        }

        if (reconciliationReady === false) {
          // Not persisted (we already returned for persisted orders): show a warning.
          // If the backend provided warnings, prefer them as the "reason".
          const warnings = extractWarnings(metaAny)
          const reason =
            warnings.length > 0
              ? warnings.join('; ')
              : readinessReason || t('common.toast.uploadNotReady.reasons.unknown')
          push({
            variant: 'warning',
            title: t('common.toast.uploadNotReady.title'),
            description: t('common.toast.uploadNotReady.description', { reason }),
          })
          return
        }

        push({
          variant: 'success',
          title: t('common.toast.upload.title'),
          description: t('common.toast.upload.description'),
        })
      } catch (error) {
        push(createErrorMessage(t, error))
      } finally {
        setProcessing(false)
      }
    },
    [actorId, onResult, push, strategy, t, uploadMode, useDebugEndpoint, useMockData]
  )

  return (
    <div className="panel">
      <div className="flex items-center gap-4 mb-6">
        <div className="w-12 h-12 bg-gradient-to-br from-yellow-500 to-orange-500 rounded-full flex items-center justify-center flex-shrink-0 shadow-lg">
          <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
            />
          </svg>
        </div>
        <div>
          <h3 className="text-body font-bold mb-1">{t('order.upload.title')}</h3>
          <p className="text-label">{t('order.upload.description')}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="sm:col-span-1">
            <div className="text-label mb-1">{t('order.upload.mode')}</div>
            <div className="grid grid-cols-2 w-full rounded-md border border-[color:var(--bg-card-border)] overflow-hidden">
              <button
                type="button"
                className={`px-3 py-2 text-sm font-medium transition-colors whitespace-nowrap w-full text-center truncate ${
                  uploadMode === 'pdf'
                    ? 'bg-[color:var(--color-gold)] text-white'
                    : 'bg-transparent text-[color:var(--text-primary)]'
                }`}
                onClick={() => setUploadMode('pdf')}
                disabled={isBusy}
              >
                {t('order.upload.modes.pdf')}
              </button>
              <button
                type="button"
                className={`px-3 py-2 text-sm font-medium transition-colors whitespace-nowrap w-full text-center truncate border-l border-[color:var(--bg-card-border)] ${
                  uploadMode === 'images'
                    ? 'bg-[color:var(--color-gold)] text-white'
                    : 'bg-transparent text-[color:var(--text-primary)]'
                }`}
                onClick={() => setUploadMode('images')}
                disabled={isBusy}
              >
                {t('order.upload.modes.images')}
              </button>
            </div>
          </div>

          <div className="sm:col-span-2">
            <div className="text-label mb-1">{t('order.upload.strategy')}</div>
            <div className="grid grid-cols-4 w-full rounded-md border border-[color:var(--bg-card-border)] overflow-hidden">
              <button
                type="button"
                className={`px-3 py-2 text-sm font-medium transition-colors w-full text-center truncate ${
                  strategy === 'auto'
                    ? 'bg-[color:var(--color-gold)] text-white'
                    : 'bg-transparent text-[color:var(--text-primary)]'
                }`}
                onClick={() => setStrategy('auto')}
                disabled={isBusy}
              >
                {t('order.upload.strategies.auto')}
              </button>
              <button
                type="button"
                className={`px-3 py-2 text-sm font-medium transition-colors w-full text-center truncate border-l border-[color:var(--bg-card-border)] ${
                  strategy === 'manual'
                    ? 'bg-[color:var(--color-gold)] text-white'
                    : 'bg-transparent text-[color:var(--text-primary)]'
                }`}
                onClick={() => setStrategy('manual')}
                disabled={isBusy}
              >
                {t('order.upload.strategies.manual')}
              </button>
              <button
                type="button"
                className={`px-3 py-2 text-sm font-medium transition-colors w-full text-center truncate border-l border-[color:var(--bg-card-border)] ${
                  strategy === 'cloud'
                    ? 'bg-[color:var(--color-gold)] text-white'
                    : 'bg-transparent text-[color:var(--text-primary)]'
                }`}
                onClick={() => setStrategy('cloud')}
                disabled={isBusy}
              >
                {t('order.upload.strategies.cloud')}
              </button>
              <button
                type="button"
                className={`px-3 py-2 text-sm font-medium transition-colors w-full text-center truncate border-l border-[color:var(--bg-card-border)] ${
                  strategy === 'local'
                    ? 'bg-[color:var(--color-gold)] text-white'
                    : 'bg-transparent text-[color:var(--text-primary)]'
                }`}
                onClick={() => setStrategy('local')}
                disabled={isBusy}
              >
                {t('order.upload.strategies.local')}
              </button>
            </div>
          </div>
        </div>

        <ToggleSwitch
          checked={useDebugEndpoint}
          onChange={setUseDebugEndpoint}
          disabled={isBusy}
          label={t('order.upload.includeDebug')}
        />

        <ToggleSwitch
          checked={useMockData}
          onChange={setUseMockData}
          disabled={isBusy}
          label={t('order.upload.useMock')}
        />

        <input
          ref={fileInputRef}
          type="file"
          accept={
            uploadMode === 'pdf' ? 'application/pdf,.pdf' : 'image/png,image/jpeg,image/webp,.png,.jpg,.jpeg,.webp'
          }
          multiple={uploadMode === 'images'}
          className="hidden"
          onChange={e => {
            const files = Array.from(e.target.files ?? [])
            e.target.value = ''
            void onFileSelected(files)
          }}
        />

        <button className="btn w-full" onClick={onPickFile} disabled={isBusy}>
          {isBusy ? (
            <>
              <InlineSpinner />
              {t('common.status.uploading')}
            </>
          ) : uploadMode === 'pdf' ? (
            t('order.upload.action')
          ) : (
            t('order.upload.actionImages')
          )}
        </button>

        {isBusy ? (
          <div className="mt-3 flex items-center gap-2 text-sm text-[color:var(--text-secondary)]">
            <InlineSpinner size={16} />
            {t('order.upload.processing')}
          </div>
        ) : null}
      </div>
    </div>
  )
}
