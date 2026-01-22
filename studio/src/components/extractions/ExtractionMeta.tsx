import type { ExtractionRow } from '../../services/core/extraction/types'

type Translator = (key: string, options?: Record<string, unknown>) => string

type Props = {
  row: ExtractionRow
  t: Translator
  certificateId?: string | null
}

export default function ExtractionMeta({ row, t, certificateId }: Props) {
  return (
    <div className="mb-5 rounded-md border border-[color:var(--bg-card-border)] bg-white/35 dark:bg-white/5 px-3 py-2">
      {certificateId ? (
        <div>
          <div className="text-xs text-[color:var(--text-secondary)]">{t('extraction.detail.certificateIdLabel')}</div>
          <div className="text-sm font-medium break-words">{certificateId}</div>
        </div>
      ) : null}

      {row.error ? (
        <div className="mt-2 rounded-md border border-red-500/30 bg-red-500/10 px-2 py-1">
          <div className="text-xs text-[color:var(--text-secondary)]">{t('common.status.error')}</div>
          <div className="text-sm font-medium break-words text-red-800 dark:text-red-200">{row.error}</div>
        </div>
      ) : null}

      <div className={certificateId || row.error ? 'mt-3' : ''}>
        <div className="text-xs text-[color:var(--text-secondary)]">{t('extraction.detail.strategyTitle')}</div>
        <div className="text-sm font-medium break-words">{row.strategy_used || '-'}</div>
      </div>
    </div>
  )
}
