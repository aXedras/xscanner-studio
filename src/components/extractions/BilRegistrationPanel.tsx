import { useMemo, useState } from 'react'
import { formatDateTimeShort } from '../../lib/utils/date'
import { Modal } from '../ui/Modal'
import type { BilRegistrationRow, ExtractionRow } from '../../services/core/extraction/types'

export type BilRegistrationPanelProps = {
  versions: ExtractionRow[]
  byExtractionId: Record<string, BilRegistrationRow[]>
  loading: boolean
  error: string | null
  selectedExtractionId: string | null
  onSelectExtractionId: (extractionId: string | null) => void
  language: string
  t: (key: string) => string
}

export function BilRegistrationPanel(props: BilRegistrationPanelProps) {
  const { versions, byExtractionId, loading, error, selectedExtractionId, onSelectExtractionId, language, t } = props

  const [showAll, setShowAll] = useState(false)

  const versionsWithAttempts = useMemo(() => {
    return versions.filter(v => (byExtractionId[String(v.id)] ?? []).length > 0)
  }, [byExtractionId, versions])

  const selectedAttempts = selectedExtractionId ? (byExtractionId[selectedExtractionId] ?? []) : []
  const visibleAttempts = showAll ? selectedAttempts : selectedAttempts.slice(0, 5)

  const selectedVersion = useMemo(() => {
    if (!selectedExtractionId) return null
    return versions.find(v => String(v.id) === selectedExtractionId) ?? null
  }, [selectedExtractionId, versions])

  const modalTitle = useMemo(() => {
    if (!selectedVersion) return t('extraction.detail.bil.details')
    const count = selectedAttempts.length
    const when = formatDateTimeShort(selectedVersion.created_at, language)
    return `${t('extraction.detail.bil.details')} (${count}) — ${when}`
  }, [language, selectedAttempts.length, selectedVersion, t])

  const renderJsonSection = (label: string, value: unknown, options?: { defaultOpen?: boolean }) => {
    if (value == null) return null
    return (
      <details className="mt-2" open={options?.defaultOpen}>
        <summary className="cursor-pointer text-label">{label}</summary>
        <pre className="mt-2 p-3 rounded-md border border-[color:var(--bg-card-border)] bg-[color:var(--bg-primary)] text-xs text-[color:var(--text-primary)] overflow-auto max-h-[45vh]">
          {JSON.stringify(value, null, 2)}
        </pre>
      </details>
    )
  }

  const resultBadgeClass = (success: boolean): string => {
    return success
      ? 'border-emerald-500/40 text-emerald-800 dark:text-emerald-300 bg-emerald-500/10'
      : 'border-red-500/40 text-red-800 dark:text-red-300 bg-red-500/10'
  }

  return (
    <div className="mt-6">
      <h3 className="text-body font-bold mb-2">{t('extraction.detail.bil.title')}</h3>

      {loading ? (
        <div className="text-label">{t('common.status.loading')}</div>
      ) : error ? (
        <div className="text-label text-red-600">{error}</div>
      ) : versionsWithAttempts.length === 0 ? (
        <div className="text-label">{t('extraction.detail.bil.empty')}</div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="text-left">
                <tr className="table-divider-strong">
                  <th className="py-2 pr-4 whitespace-nowrap">{t('extraction.detail.bil.version')}</th>
                  <th className="py-2 pr-4 whitespace-nowrap">{t('extraction.detail.bil.result')}</th>
                  <th className="py-2 pr-4 whitespace-nowrap">{t('extraction.detail.bil.certificateId')}</th>
                </tr>
              </thead>
              <tbody>
                {versionsWithAttempts.map(v => {
                  const attempts = byExtractionId[String(v.id)] ?? []
                  const last = attempts[0] ?? null
                  const lastCert = attempts.find(a => a.success && a.certificate_id)?.certificate_id ?? null
                  const isSelected = selectedExtractionId === String(v.id)
                  return (
                    <tr
                      key={v.id}
                      className={`table-divider cursor-pointer ${
                        isSelected ? 'bg-[rgb(var(--color-gold-rgb)/0.08)]' : ''
                      }`}
                      onClick={() => {
                        setShowAll(false)
                        onSelectExtractionId(isSelected ? null : String(v.id))
                      }}
                    >
                      <td className="py-2 pr-4 whitespace-nowrap">{formatDateTimeShort(v.created_at, language)}</td>
                      <td className="py-2 pr-4 whitespace-nowrap">
                        {last ? (last.success ? t('common.status.success') : t('common.status.error')) : '-'}
                      </td>
                      <td className="py-2 pr-4 whitespace-nowrap">{lastCert ?? '-'}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          <Modal
            open={Boolean(selectedExtractionId)}
            title={modalTitle}
            closeLabel={t('common.action.close')}
            onClose={() => {
              setShowAll(false)
              onSelectExtractionId(null)
            }}
          >
            {selectedAttempts.length > 5 ? (
              <div className="flex items-center justify-end mb-3">
                <button type="button" className="btn btn-outline" onClick={() => setShowAll((prev: boolean) => !prev)}>
                  {showAll ? t('common.action.close') : t('common.action.showDetails')}
                </button>
              </div>
            ) : null}

            {selectedAttempts.length === 0 ? (
              <div className="text-label">{t('extraction.detail.bil.empty')}</div>
            ) : (
              <div className="space-y-4">
                {visibleAttempts.map(item => (
                  <div
                    key={item.id}
                    className="rounded-xl border border-[color:var(--bg-card-border)] bg-[color:var(--bg-primary)] px-4 py-3"
                  >
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                      <div className="text-sm font-medium">{formatDateTimeShort(item.created_at, language)}</div>
                      <span
                        className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold ${resultBadgeClass(
                          Boolean(item.success)
                        )}`}
                      >
                        {item.success ? t('common.status.success') : t('common.status.error')}
                      </span>
                    </div>

                    <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="min-w-0">
                        <div className="rounded-md border border-[color:var(--bg-card-border)] bg-white/35 p-3 dark:bg-white/5">
                          <div className="text-label">{t('extraction.detail.bil.certificateId')}</div>
                          <div className="text-body font-semibold break-all">{item.certificate_id ?? '-'}</div>
                        </div>

                        {renderJsonSection(t('extraction.detail.bil.payloadReceived'), item.payload_received, {
                          defaultOpen: true,
                        })}
                        {renderJsonSection(t('extraction.detail.bil.payloadSent'), item.payload_sent)}
                      </div>

                      <div className="min-w-0">
                        <div className="space-y-1 text-label">
                          <div>
                            {t('extraction.detail.bil.source')}: {item.trigger_source}
                          </div>
                          <div>
                            {t('extraction.detail.bil.processingTime')}:{' '}
                            {typeof item.processing_time === 'number' ? item.processing_time.toFixed(3) : '-'}
                          </div>
                          <div>
                            {t('extraction.detail.bil.httpStatus')}: {item.http_status ?? '-'}
                          </div>
                          {item.endpoint ? <div>{item.endpoint}</div> : null}
                        </div>

                        {item.error ? <div className="mt-3 text-red-600">{item.error}</div> : null}
                        {renderJsonSection(t('extraction.detail.bil.errorDetails'), item.error_details)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Modal>
        </>
      )}
    </div>
  )
}
