import { DateRangePicker } from '../../components/ui/DateRangePicker'
import { MultiSelectMenu } from '../../components/ui/MultiSelectMenu'
import { ExtractionStatusBadge } from '../../components/extractions/ExtractionStatusBadge'
import type { ExtractionStatus } from '../../services/core/extraction/types'
import { getExtractionStatusLabelKey } from '../../services/core/extraction/types'
import type { TFunction } from 'i18next'

type Props = {
  show: boolean
  t: TFunction
  language: string

  createdAtFrom: string
  createdAtTo: string
  onDateRangeChange: (from: string, to: string) => void

  statusFilters: ExtractionStatus[]
  onStatusFiltersChange: (next: ExtractionStatus[]) => void
}

export function ExtractionsTableFilters({
  show,
  t,
  language,
  createdAtFrom,
  createdAtTo,
  onDateRangeChange,
  statusFilters,
  onStatusFiltersChange,
}: Props) {
  if (!show) return null

  return (
    <div className="rounded-md border border-[color:var(--bg-card-border)] bg-white/35 p-3 dark:bg-white/5">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div>
          <div className="text-label mb-2">{t('common.fields.createdAt')}</div>
          <DateRangePicker
            label={t('common.fields.createdAt')}
            fromLabel={t('common.fields.from')}
            toLabel={t('common.fields.to')}
            resetLabel={t('common.action.reset')}
            language={language}
            value={{
              from: createdAtFrom.trim() ? createdAtFrom : undefined,
              to: createdAtTo.trim() ? createdAtTo : undefined,
            }}
            onChange={next => onDateRangeChange(next.from ?? '', next.to ?? '')}
          />
        </div>

        <div>
          <div className="text-label mb-2">{t('extraction.fields.status')}</div>
          <MultiSelectMenu
            label={t('extraction.fields.status')}
            selected={statusFilters}
            options={(['pending', 'corrected', 'validated', 'rejected', 'error'] as const).map(status => ({
              value: status,
              label: t(getExtractionStatusLabelKey(status)),
            }))}
            renderSelected={({ selected }) => (
              <div className="flex flex-wrap items-center gap-2">
                {selected.length === 0 ? (
                  <span className="truncate text-[color:var(--text-secondary)]">—</span>
                ) : (
                  selected.map(status => <ExtractionStatusBadge key={status} status={status} t={t} />)
                )}
              </div>
            )}
            onChange={next => onStatusFiltersChange(next)}
          />
        </div>
      </div>
    </div>
  )
}
