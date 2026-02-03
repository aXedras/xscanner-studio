import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useOutletContext, useParams } from 'react-router-dom'
import type { User } from '@supabase/supabase-js'
import { useAppTranslation, I18N_SCOPES } from '../lib/i18n'
import { services } from '../services'
import { PageHeader } from '../components/layout/PageHeader'
import { useUiMessages } from '../ui/messages/UiMessagesContext'
import { createErrorMessage } from '../ui/messages/fromError'
import InfoPanel from '../components/messages/InfoPanel'
import type { OrderItemRow, OrderRow } from '../services/core/order/types'
import {
  buildOrderUpdatePatch,
  createOrderCanonicalFieldsForm,
  type OrderCanonicalFieldsForm,
} from '../components/orders/orderCanonicalFieldsForm'
import { OrderDetailView } from '../components/orders/OrderDetailView'
import { buildOrderDebugStrings } from '../components/orders/orderExtractionDebug'

export default function OrderDetailPage() {
  const { t, i18n } = useAppTranslation(I18N_SCOPES.order)
  const { push } = useUiMessages()
  const navigate = useNavigate()
  const outlet = useOutletContext<{ user: User }>()
  const params = useParams()
  const originalId = params.originalId?.trim() ?? ''

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [order, setOrder] = useState<OrderRow | null>(null)
  const [history, setHistory] = useState<OrderRow[]>([])
  const [items, setItems] = useState<OrderItemRow[]>([])
  const itemDirtyIdsRef = useRef<Set<string>>(new Set())

  const [form, setForm] = useState<OrderCanonicalFieldsForm | null>(null)

  const [pdfSrc, setPdfSrc] = useState<string | null>(null)
  const pdfRevokeRef = useRef<(() => void) | null>(null)

  const [warningPanelDismissed, setWarningPanelDismissed] = useState(false)

  const { finalPretty, metaPretty, rawSignalsPretty, markerText, rawText, pdfText, tracePretty } = useMemo(
    () => buildOrderDebugStrings(order),
    [order]
  )

  const warningPanel = useMemo(() => {
    if (!order) return null
    if (warningPanelDismissed) return null

    const extractedAny = order.extracted_data
    const extracted =
      typeof extractedAny === 'object' && extractedAny !== null ? (extractedAny as Record<string, unknown>) : null
    const metaAny =
      extracted && typeof extracted.meta === 'object' && extracted.meta !== null
        ? (extracted.meta as Record<string, unknown>)
        : null
    const warningsAny = metaAny?.warnings
    const warnings = Array.isArray(warningsAny) ? warningsAny.filter(w => typeof w === 'string' && w.trim()) : []

    const readinessAny = metaAny?.readiness
    const readiness =
      readinessAny && typeof readinessAny === 'object' && readinessAny !== null
        ? (readinessAny as Record<string, unknown>)
        : null
    const reconciliationReady = readiness?.reconciliation_ready
    const readinessReason = readiness?.reason

    const processingErrors = warnings.filter(w => w.startsWith('processing_error='))
    const isCloudAttemptProcessingError = (w: string): boolean => {
      const s = w.toLowerCase()
      if (!s.startsWith('processing_error=')) return false
      return (
        s.includes('ai extraction failed') ||
        s.includes('aiprovidererror') ||
        s.includes('openai error') ||
        s.includes('invalid_api_key')
      )
    }

    const cloudAttemptErrors = processingErrors.filter(isCloudAttemptProcessingError)
    const otherProcessingErrors = processingErrors.filter(w => !isCloudAttemptProcessingError(w))

    const fallbackOk =
      !order.error &&
      order.status !== 'error' &&
      typeof reconciliationReady === 'boolean' &&
      reconciliationReady === true

    const cloudAttemptFailedButFallbackOk =
      fallbackOk && cloudAttemptErrors.length > 0 && otherProcessingErrors.length === 0

    const cloudErrorSummary = (() => {
      const first = cloudAttemptErrors[0]
      if (!first) return null

      const openAiStatus = /openai error\s+(\d{3})/i.exec(first)?.[1]
      const invalidApiKey = /invalid_api_key/i.test(first)
      if (openAiStatus && invalidApiKey) return `OpenAI ${openAiStatus} (invalid_api_key)`
      if (openAiStatus) return `OpenAI ${openAiStatus}`
      return 'cloud_attempt_failed'
    })()

    const hasWarning =
      warnings.length > 0 ||
      Boolean(order.error) ||
      order.status === 'error' ||
      (typeof reconciliationReady === 'boolean' && reconciliationReady === false)
    if (!hasWarning) return null

    const detailsLines: string[] = []
    if (cloudAttemptFailedButFallbackOk) {
      detailsLines.push('note=cloud_attempt_failed_manual_fallback_used')
      if (cloudErrorSummary) detailsLines.push(`cloud_error=${cloudErrorSummary}`)
    }
    if (order.status) detailsLines.push(`status=${String(order.status)}`)
    if (order.error) detailsLines.push(`error=${String(order.error)}`)
    if (typeof reconciliationReady === 'boolean') {
      detailsLines.push(`reconciliation_ready=${String(reconciliationReady)}`)
    }
    if (typeof readinessReason === 'string' && readinessReason.trim()) {
      detailsLines.push(`readiness_reason=${String(readinessReason)}`)
    }
    if (warnings.length > 0) {
      detailsLines.push('warnings:')
      for (const w of warnings) detailsLines.push(`- ${w}`)
    }

    const panelVariant: 'info' | 'warning' = cloudAttemptFailedButFallbackOk ? 'info' : 'warning'

    return {
      variant: panelVariant,
      title: t('order.detail.warningsPanel.title'),
      description: cloudAttemptFailedButFallbackOk
        ? t('order.detail.warningsPanel.descriptionFallbackOk')
        : t('order.detail.warningsPanel.description'),
      details: detailsLines.join('\n'),
    }
  }, [order, t, warningPanelDismissed])

  useEffect(() => {
    return () => {
      pdfRevokeRef.current?.()
    }
  }, [])

  useEffect(() => {
    let isMounted = true

    const run = async () => {
      if (!originalId) {
        setLoading(false)
        setOrder(null)
        return
      }

      setLoading(true)
      try {
        const [active, versions] = await Promise.all([
          services.orderService.findActiveByOriginalId(originalId),
          services.orderService.findHistoryByOriginalId(originalId),
        ])

        if (!isMounted) return

        setOrder(active)
        setHistory(versions)
        setIsEditing(false)
        setForm(active ? createOrderCanonicalFieldsForm(active, i18n.language) : null)

        if (active?.id) {
          const activeItems = await services.orderService.listActiveItemsByOriginalId(originalId)
          if (!isMounted) return
          setItems(activeItems)
        } else {
          setItems([])
        }

        pdfRevokeRef.current?.()
        pdfRevokeRef.current = null
        setPdfSrc(null)

        if (active?.storage_path) {
          const preview = await services.orderService.getPdfPreviewSrc(active.storage_path)
          if (!isMounted) return
          setPdfSrc(preview?.src ?? null)
          pdfRevokeRef.current = preview?.revoke ?? null
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
  }, [i18n.language, originalId, push, t])

  const canEdit = !!order && !loading && !saving
  const canSave = !!order && !!form && isEditing && !loading && !saving
  const canDelete = !!order && !isEditing && !loading && !saving

  const handlePatchItem = async (itemId: string, patch: Partial<OrderItemRow>) => {
    if (!order) return

    if (isEditing) {
      itemDirtyIdsRef.current.add(itemId)
    }

    // Always patch UI immediately.
    setItems(prev => prev.map(row => (row.id === itemId ? { ...row, ...patch } : row)))

    // In view-mode, persist immediately so edits don't get lost.
    if (isEditing) return

    setSaving(true)
    try {
      const savedRow = await services.orderService.updateItem(itemId, { ...patch, updated_by: outlet.user.id })
      // Item updates are versioned (new row id). Replace with returned row.
      setItems(prev => prev.map(row => (row.id === itemId ? savedRow : row)))
      push({
        variant: 'success',
        title: t('common.toast.update.title'),
        description: t('common.toast.update.description'),
        autoDismissMs: 2000,
        dismissOnNextAction: true,
      })
    } catch (error) {
      push(createErrorMessage(t, error))
    } finally {
      setSaving(false)
    }
  }

  const handleStartEdit = () => {
    if (!order) return
    setForm(createOrderCanonicalFieldsForm(order, i18n.language))
    setIsEditing(true)
  }

  const handleCancelEdit = () => {
    if (!order) return
    setForm(createOrderCanonicalFieldsForm(order, i18n.language))
    setIsEditing(false)
    itemDirtyIdsRef.current.clear()
  }

  const handleSave = async () => {
    if (!order || !form) return

    setSaving(true)
    try {
      const patch = buildOrderUpdatePatch(form)
      const hasOrderChanges = Object.keys(patch).length > 0

      if (hasOrderChanges) {
        await services.orderService.updateOrder(order.id, { ...patch, updated_by: outlet.user.id })
      }

      // Persist only items changed while in edit-mode.
      const dirtyIds = Array.from(itemDirtyIdsRef.current)
      const actorId = outlet.user.id

      for (const itemId of dirtyIds) {
        const row = items.find(it => it.id === itemId)
        if (!row) continue
        await services.orderService.updateItem(row.id, {
          serial_number: row.serial_number,
          item: row.item,
          description: row.description,
          quantity: row.quantity,
          item_price: row.item_price,
          total_price: row.total_price,
          metal: row.metal,
          weight: row.weight,
          weight_unit: row.weight_unit,
          fineness: row.fineness,
          producer: row.producer,
          form: row.form,
          updated_by: actorId,
        })
      }

      const [freshActive, versions] = await Promise.all([
        services.orderService.findActiveByOriginalId(originalId),
        services.orderService.findHistoryByOriginalId(originalId),
      ])

      setOrder(freshActive)
      setHistory(versions)
      setForm(freshActive ? createOrderCanonicalFieldsForm(freshActive, i18n.language) : null)
      setIsEditing(false)
      itemDirtyIdsRef.current.clear()

      if (freshActive?.id) {
        const freshItems = await services.orderService.listActiveItemsByOriginalId(originalId)
        setItems(freshItems)
      } else {
        setItems([])
      }
    } catch (error) {
      push(createErrorMessage(t, error))
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!order) return
    if (!window.confirm(t('order.detail.deleteConfirm'))) return

    setSaving(true)
    try {
      await services.orderService.updateOrder(order.id, {
        is_active: false,
        status: 'closed',
        updated_by: outlet.user.id,
      })

      push({
        variant: 'success',
        title: t('common.toast.delete.title'),
        description: t('common.toast.delete.description'),
        autoDismissMs: 2500,
        dismissOnNextAction: true,
      })

      navigate('/orders')
    } catch (error) {
      push(createErrorMessage(t, error))
    } finally {
      setSaving(false)
    }
  }

  if (!originalId) {
    return (
      <div>
        <PageHeader
          title={t('order.detail.title')}
          subtitle={t('order.detail.missingId')}
          backLabel={t('common.action.back')}
        />
        <div className="panel">{t('order.detail.missingId')}</div>
      </div>
    )
  }

  return (
    <div>
      <PageHeader
        title={t('order.detail.title')}
        subtitle={t('order.detail.subtitle', { originalId })}
        backLabel={t('common.action.back')}
      />

      {!loading && warningPanel ? (
        <div className="sticky top-4 z-20 mb-4">
          <InfoPanel
            variant={warningPanel.variant}
            title={warningPanel.title}
            description={warningPanel.description}
            details={warningPanel.details}
            closeLabel={t('common.action.close')}
            onClose={() => setWarningPanelDismissed(true)}
          />
        </div>
      ) : null}

      {loading ? <div className="panel">{t('common.status.loading')}</div> : null}

      {!loading && !order ? <div className="panel">{t('order.detail.notFound')}</div> : null}

      {!loading && order ? (
        <OrderDetailView
          t={t}
          language={i18n.language}
          order={order}
          history={history}
          items={items}
          currentUserId={outlet.user.id}
          pdfSrc={pdfSrc}
          isEditing={isEditing}
          saving={saving}
          canEdit={canEdit}
          canSave={canSave}
          canDelete={canDelete}
          form={form}
          onFormChange={setForm}
          onStartEdit={handleStartEdit}
          onCancelEdit={handleCancelEdit}
          onSave={handleSave}
          onDelete={handleDelete}
          onPatchItem={handlePatchItem}
          loadItemHistory={services.orderService.findItemHistoryByOriginalId.bind(services.orderService)}
          finalPretty={finalPretty}
          metaPretty={metaPretty}
          rawSignalsPretty={rawSignalsPretty}
          markerText={markerText}
          rawText={rawText}
          pdfText={pdfText}
          tracePretty={tracePretty}
        />
      ) : null}
    </div>
  )
}
