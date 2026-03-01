import { useMemo, useRef, useState } from 'react'
import type { TFunction } from 'i18next'

import { Modal } from '../ui/Modal'
import { ActionIconButton } from '../ui/ActionIconButton'
import { CodeIcon, CopyIcon, RegisterIcon, RejectIcon } from '../ui/ActionIcons'

import { OrderKpiView } from './OrderKpiView'
import { FieldMappingView } from './FieldMappingView'
import { extractFieldMapping, formatFieldMappingForUi } from './orderFieldMappingDebug'
import { buildOrderKpiCopyText } from './orderKpis'
import { TraceTreeView } from './TraceTreeView'
import { parseTrace } from './orderTraceDebug'
import { RawSignalsTable } from './RawSignalsTable'

type DebugTabKey = 'final' | 'meta' | 'mapping' | 'raw' | 'markerText' | 'rawText' | 'pdfText' | 'kpi' | 'trace'

type Props = {
  open: boolean
  onClose: () => void
  t: TFunction
  language: string

  finalPretty: string
  metaPretty: string
  rawSignalsPretty: string
  markerText: string
  rawText: string
  pdfText: string
  tracePretty: string
}

async function copyToClipboard(text: string): Promise<void> {
  if (!text) return

  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text)
    return
  }

  // Fallback for older browsers / non-secure contexts.
  const el = document.createElement('textarea')
  el.value = text
  el.setAttribute('readonly', 'true')
  el.style.position = 'fixed'
  el.style.left = '-9999px'
  document.body.appendChild(el)
  el.select()
  document.execCommand('copy')
  document.body.removeChild(el)
}

function TabButton(props: { active: boolean; label: string; onClick: () => void }) {
  const { active, label, onClick } = props
  return (
    <button
      type="button"
      onClick={onClick}
      className={
        active
          ? 'btn btn-sm bg-[color:var(--bg-accent)] text-white border-[color:var(--bg-accent)]'
          : 'btn btn-outline btn-sm'
      }
    >
      {label}
    </button>
  )
}

export function OrderDebugModal(props: Props) {
  const { open, onClose, t, language, finalPretty, metaPretty, rawSignalsPretty, markerText, rawText, tracePretty } =
    props
  const { pdfText } = props

  const initialTab: DebugTabKey = useMemo(() => {
    if (finalPretty) return 'final'
    if (rawSignalsPretty) return 'raw'
    return 'trace'
  }, [finalPretty, rawSignalsPretty])

  const [tab, setTab] = useState<DebugTabKey>(initialTab)
  const [showJson, setShowJson] = useState(false)
  const [copied, setCopied] = useState(false)
  const copiedTimerRef = useRef<number | null>(null)

  const title = t('order.detail.debugDialogTitle')

  const metaAny = useMemo((): unknown => {
    if (!metaPretty) return null
    try {
      return JSON.parse(metaPretty)
    } catch {
      return null
    }
  }, [metaPretty])

  const traceRoot = useMemo(() => parseTrace(tracePretty), [tracePretty])

  const finalAny = useMemo((): unknown => {
    if (!finalPretty) return null
    try {
      return JSON.parse(finalPretty)
    } catch {
      return null
    }
  }, [finalPretty])

  const mappingPretty = useMemo((): string => {
    const mapping = extractFieldMapping(metaAny)
    if (!mapping) return ''
    try {
      return JSON.stringify(formatFieldMappingForUi(mapping), null, 2)
    } catch {
      return String(mapping)
    }
  }, [metaAny])

  const mappingAny = useMemo((): unknown => extractFieldMapping(metaAny), [metaAny])

  const activeText = (() => {
    if (tab === 'final') return finalPretty || '{}'
    if (tab === 'meta') return metaPretty || ''
    if (tab === 'mapping') return mappingPretty || ''
    if (tab === 'raw') return rawSignalsPretty || '{}'
    if (tab === 'markerText') return markerText || ''
    if (tab === 'rawText') return rawText || ''
    if (tab === 'pdfText') return pdfText || ''
    if (tab === 'kpi') return buildOrderKpiCopyText(traceRoot, metaAny)
    return tracePretty || ''
  })()

  const handleCopy = async () => {
    try {
      await copyToClipboard(activeText)
      setCopied(true)

      if (copiedTimerRef.current) window.clearTimeout(copiedTimerRef.current)
      copiedTimerRef.current = window.setTimeout(() => {
        setCopied(false)
      }, 1200)
    } catch {
      // Intentionally ignore; copying is best-effort.
    }
  }

  const body = (() => {
    if (showJson) {
      return activeText ? (
        <pre className="text-xs whitespace-pre-wrap break-all">{activeText}</pre>
      ) : (
        <div className="text-sm text-[color:var(--text-secondary)]">{t('order.detail.debugEmpty')}</div>
      )
    }

    if (tab === 'final') {
      return <pre className="text-xs whitespace-pre-wrap break-all">{finalPretty || '{}'}</pre>
    }
    if (tab === 'meta') {
      return metaPretty ? (
        <pre className="text-xs whitespace-pre-wrap break-all">{metaPretty}</pre>
      ) : (
        <div className="text-sm text-[color:var(--text-secondary)]">{t('order.detail.metaEmpty')}</div>
      )
    }
    if (tab === 'mapping') {
      return mappingAny ? (
        <FieldMappingView mapping={mappingAny} finalData={finalAny} t={t} />
      ) : (
        <div className="text-sm text-[color:var(--text-secondary)]">{t('order.detail.mappingEmpty')}</div>
      )
    }
    if (tab === 'raw') {
      return <RawSignalsTable rawSignalsPretty={rawSignalsPretty} t={t} />
    }
    if (tab === 'markerText') {
      return markerText ? (
        <pre className="text-xs whitespace-pre-wrap break-all">{markerText}</pre>
      ) : (
        <div className="text-sm text-[color:var(--text-secondary)]">{t('order.detail.markerTextEmpty')}</div>
      )
    }
    if (tab === 'rawText') {
      return rawText ? (
        <pre className="text-xs whitespace-pre-wrap break-all">{rawText}</pre>
      ) : (
        <div className="text-sm text-[color:var(--text-secondary)]">{t('order.detail.rawTextEmpty')}</div>
      )
    }
    if (tab === 'pdfText') {
      return pdfText ? (
        <pre className="text-xs whitespace-pre-wrap break-all">{pdfText}</pre>
      ) : (
        <div className="text-sm text-[color:var(--text-secondary)]">{t('order.detail.rawTextEmpty')}</div>
      )
    }
    if (tab === 'kpi') {
      if (!traceRoot) {
        return <div className="text-sm text-[color:var(--text-secondary)]">{t('order.detail.traceEmpty')}</div>
      }

      return <OrderKpiView trace={traceRoot} meta={metaAny} t={t} language={language} />
    }
    if (!traceRoot) {
      return <div className="text-sm text-[color:var(--text-secondary)]">{t('order.detail.traceEmpty')}</div>
    }

    const resolveArtifactRef = (ref: string): { value: string; contentType?: string } | null => {
      if (ref === 'extracted_data.raw.raw_text') return { value: rawText ?? '', contentType: 'text/plain' }
      if (ref === 'extracted_data.raw.marker_text') return { value: markerText ?? '', contentType: 'text/plain' }
      if (ref === 'extracted_data.raw.pdf_text') return { value: pdfText ?? '', contentType: 'text/plain' }
      return null
    }

    return <TraceTreeView root={traceRoot} resolveArtifactRef={resolveArtifactRef} />
  })()

  return (
    <Modal
      open={open}
      title={title}
      onClose={onClose}
      closeLabel={t('common.action.close')}
      hideCloseButton
      headerActions={
        <div className="flex items-center gap-2">
          <ActionIconButton
            label={showJson ? t('common.action.viewUi') : t('common.action.viewJson')}
            onClick={() => setShowJson(v => !v)}
          >
            <CodeIcon />
          </ActionIconButton>
          <ActionIconButton
            label={copied ? t('common.action.copied') : t('common.action.copy')}
            onClick={handleCopy}
            inactive={!activeText}
          >
            {copied ? <RegisterIcon /> : <CopyIcon />}
          </ActionIconButton>
          <ActionIconButton label={t('common.action.close')} onClick={onClose}>
            <RejectIcon />
          </ActionIconButton>
        </div>
      }
      widthClassName="max-w-6xl"
    >
      <div className="flex flex-col h-[70vh]">
        <div className="flex flex-wrap items-center gap-2 mb-3 shrink-0">
          <TabButton
            active={tab === 'final'}
            label={t('order.detail.debugFinalTitle')}
            onClick={() => setTab('final')}
          />
          <TabButton active={tab === 'trace'} label={t('order.detail.traceTitle')} onClick={() => setTab('trace')} />
          <TabButton active={tab === 'kpi'} label={t('order.detail.kpi.title')} onClick={() => setTab('kpi')} />
          <TabButton active={tab === 'meta'} label={t('order.detail.metaTitle')} onClick={() => setTab('meta')} />
          <TabButton
            active={tab === 'mapping'}
            label={t('order.detail.mappingTitle')}
            onClick={() => setTab('mapping')}
          />
          <TabButton
            active={tab === 'rawText'}
            label={t('order.detail.rawTextTitle')}
            onClick={() => setTab('rawText')}
          />
          <TabButton
            active={tab === 'pdfText'}
            label={t('order.detail.pdfTextTitle')}
            onClick={() => setTab('pdfText')}
          />
          <TabButton
            active={tab === 'markerText'}
            label={t('order.detail.markerTextTitle')}
            onClick={() => setTab('markerText')}
          />
          <TabButton active={tab === 'raw'} label={t('order.detail.rawSignalsTitle')} onClick={() => setTab('raw')} />
        </div>

        <div className="rounded-md border border-[color:var(--bg-card-border)] bg-[color:var(--bg-card)] p-3 flex-1 overflow-auto">
          {body}
        </div>

        <div className="mt-3 text-xs text-[color:var(--text-secondary)] shrink-0">
          {t('order.detail.debugDialogHint')}
        </div>
      </div>
    </Modal>
  )
}
