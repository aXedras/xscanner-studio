import { useCallback, useEffect, useState } from 'react'
import { useParams, useOutletContext } from 'react-router-dom'
import { useAppTranslation, I18N_SCOPES } from '../lib/i18n'
import { services } from '../services'
import type { ExtractionCorrectionInput, ExtractionRow } from '../services/core/extraction/types'
import ImageInspector from '../components/images/ImageInspector'
import ExtractionMeta from '../components/extractions/ExtractionMeta'
import { ExtractionStatusBadge } from '../components/extractions/ExtractionStatusBadge'
import { ConfidenceBadge } from '../components/extractions/ConfidenceBadge'
import { BilRegistrationPanel } from '../components/extractions/BilRegistrationPanel'
import { ExtractionHistoryTable } from '../components/extractions/ExtractionHistoryTable'
import { ExtractionFieldsEditor } from '../components/extractions/ExtractionFieldsEditor'
import { ExtractionDetailActions } from '../components/extractions/ExtractionDetailActions'
import { useBilRegistrationState } from './extractions/useBilRegistrationState'
import { useUiMessages } from '../ui/messages/UiMessagesContext'
import { createErrorMessage } from '../ui/messages/fromError'
import { PageHeader } from '../components/layout/PageHeader'
import type { AuthSessionUser } from '../services/core/auth/types'

export default function ExtractionDetailPage() {
  const { t, i18n } = useAppTranslation(I18N_SCOPES.extraction)
  const { push } = useUiMessages()
  const { originalId } = useParams()
  const outlet = useOutletContext<{ user: AuthSessionUser }>()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [registering, setRegistering] = useState(false)
  const [rejecting, setRejecting] = useState(false)
  const [active, setActive] = useState<ExtractionRow | null>(null)
  const [history, setHistory] = useState<ExtractionRow[]>([])
  const [showRawJson, setShowRawJson] = useState(false)
  const isImmutable = Boolean(active && (active.status === 'validated' || active.status === 'rejected'))
  const [form, setForm] = useState<ExtractionCorrectionInput>({
    serial_number: null,
    metal: null,
    weight: null,
    weight_unit: null,
    fineness: null,
    producer: null,
  })
  const [imageUrl, setImageUrl] = useState<string | null>(null)
  const bil = useBilRegistrationState({ versions: history, activeId: active ? String(active.id) : null })

  useEffect(() => {
    let isMounted = true
    const run = async () => {
      if (!active) {
        if (isMounted) setImageUrl(null)
        return
      }

      try {
        const preview = await services.extractionService.getImagePreviewSrc(active.storage_path)
        if (!isMounted) return
        setImageUrl(preview?.src ?? null)
      } catch (error) {
        if (!isMounted) return
        setImageUrl(null)
        push(createErrorMessage(t, error))
      }
    }

    run()
    return () => {
      isMounted = false
    }
  }, [active, push, t])

  useEffect(() => {
    if (!originalId) return

    let isMounted = true

    const run = async () => {
      setLoading(true)
      try {
        const [activeRow, versions] = await Promise.all([
          services.extractionService.getActiveByOriginalId(originalId),
          services.extractionService.getHistoryByOriginalId(originalId),
        ])

        if (!isMounted) return

        setActive(activeRow)
        setHistory(versions)

        if (activeRow) {
          setForm({
            serial_number: activeRow.serial_number,
            metal: activeRow.metal,
            weight: activeRow.weight,
            weight_unit: activeRow.weight_unit,
            fineness: activeRow.fineness,
            producer: activeRow.producer,
          })
        }
      } catch (error) {
        push(createErrorMessage(t, error))
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    run()
    return () => {
      isMounted = false
    }
  }, [originalId, push, t])

  const onChange = useCallback((key: keyof ExtractionCorrectionInput, value: string) => {
    setForm(prev => ({ ...prev, [key]: value.trim() ? value : null }))
  }, [])

  const onSave = useCallback(async () => {
    if (!originalId) return
    setSaving(true)
    try {
      const updated = await services.extractionService.createCorrectionVersion({
        originalId,
        corrected: form,
        updatedBy: outlet.user.id,
      })

      // Refresh state after save
      const versions = await services.extractionService.getHistoryByOriginalId(originalId)
      setActive(updated)
      setHistory(versions)

      push({
        variant: 'success',
        title: t('common.toast.save.title'),
        description: t('common.toast.save.description'),
      })
    } catch (error) {
      push(createErrorMessage(t, error))
    } finally {
      setSaving(false)
    }
  }, [form, originalId, outlet.user.id, push, t])

  const onRegister = useCallback(async () => {
    if (!originalId) return
    setRegistering(true)
    try {
      const updated = await services.extractionService.validateActive({ originalId, updatedBy: outlet.user.id })
      const versions = await services.extractionService.getHistoryByOriginalId(originalId)
      setActive(updated)
      setHistory(versions)

      push({
        variant: 'success',
        title: t('common.toast.update.title'),
        description: t('common.toast.update.description'),
      })
    } catch (error) {
      push(createErrorMessage(t, error))
      try {
        const [activeRow, versions] = await Promise.all([
          services.extractionService.getActiveByOriginalId(originalId),
          services.extractionService.getHistoryByOriginalId(originalId),
        ])
        setActive(activeRow)
        setHistory(versions)
      } catch (refreshError) {
        push(createErrorMessage(t, refreshError))
      }
    } finally {
      setRegistering(false)
    }
  }, [originalId, outlet.user.id, push, t])

  const onReject = useCallback(async () => {
    if (!originalId) return
    setRejecting(true)
    try {
      const updated = await services.extractionService.rejectActive({ originalId, updatedBy: outlet.user.id })
      const versions = await services.extractionService.getHistoryByOriginalId(originalId)
      setActive(updated)
      setHistory(versions)

      push({
        variant: 'success',
        title: t('common.toast.update.title'),
        description: t('common.toast.update.description'),
      })
    } catch (error) {
      push(createErrorMessage(t, error))
    } finally {
      setRejecting(false)
    }
  }, [originalId, outlet.user.id, push, t])

  if (!originalId) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="panel">{t('extraction.detail.missingId')}</div>
      </div>
    )
  }

  return (
    <div>
      <PageHeader
        title={t('extraction.detail.title')}
        subtitle={t('extraction.detail.subtitle', { originalId })}
        backLabel={t('common.action.back')}
        right={
          <ExtractionDetailActions
            disabled={isImmutable}
            saving={saving}
            loading={loading}
            registering={registering}
            rejecting={rejecting}
            hasActive={Boolean(active)}
            t={(key: string) => t(key)}
            onSave={onSave}
            onRegister={onRegister}
            onReject={onReject}
          />
        }
      />

      {loading ? (
        <div className="panel">{t('common.status.loading')}</div>
      ) : !active ? (
        <div className="panel">{t('extraction.detail.notFound')}</div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="panel">
            {imageUrl ? (
              <ImageInspector
                src={imageUrl}
                alt={t('extraction.detail.imageAlt')}
                previewMaxHeight={720}
                labels={{
                  inspect: t('common.imageInspector.inspect'),
                  close: t('common.imageInspector.close'),
                  reset: t('common.imageInspector.reset'),
                  zoomIn: t('common.imageInspector.zoomIn'),
                  zoomOut: t('common.imageInspector.zoomOut'),
                  zoom: t('common.imageInspector.zoom'),
                  hint: t('common.imageInspector.hint'),
                }}
              />
            ) : (
              <div className="text-label">{t('extraction.detail.imageUnavailable')}</div>
            )}
          </div>

          <div className="panel">
            <div className="mb-3 flex flex-wrap items-center justify-start gap-2">
              <ExtractionStatusBadge status={active.status} t={t} />
              <ConfidenceBadge confidence={active.confidence} label={t('extraction.fields.confidence')} showLabel />
            </div>
            <ExtractionMeta row={active} t={t} certificateId={bil.certificateId} />
            <ExtractionFieldsEditor
              form={form}
              disabled={isImmutable}
              saving={saving}
              t={(key: string) => t(key)}
              onChange={onChange}
            />
            <ExtractionHistoryTable
              history={history}
              currentUserId={outlet.user.id}
              language={i18n.language}
              t={(key: string) => t(key)}
            />
            <BilRegistrationPanel
              versions={history}
              byExtractionId={bil.byExtractionId}
              loading={bil.loading}
              error={bil.error}
              selectedExtractionId={bil.selectedExtractionId}
              onSelectExtractionId={bil.setSelectedExtractionId}
              language={i18n.language}
              t={(key: string) => t(key)}
            />

            {active.extracted_data ? (
              <div className="mt-4">
                <button
                  type="button"
                  className="flex items-center gap-1 text-xs text-[color:var(--text-secondary)] hover:text-[color:var(--text-primary)] transition-colors"
                  onClick={() => setShowRawJson(prev => !prev)}
                >
                  <svg
                    className={`w-3 h-3 transition-transform ${showRawJson ? 'rotate-90' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  {t('extraction.detail.rawJsonTitle')}
                </button>
                {showRawJson ? (
                  <pre className="mt-2 p-3 rounded-md bg-gray-100 dark:bg-gray-800 text-xs overflow-auto max-h-96 border border-[color:var(--bg-card-border)]">
                    {JSON.stringify(active.extracted_data, null, 2)}
                  </pre>
                ) : null}
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  )
}
