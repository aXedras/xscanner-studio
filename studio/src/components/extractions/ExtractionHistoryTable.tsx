import { formatDateTimeShort } from '../../lib/utils/date'
import type { ExtractionRow } from '../../services/core/extraction/types'

function formatActor(updatedBy: string | null, currentUserId: string, t: (key: string) => string): string {
  if (!updatedBy) return t('extraction.detail.audit.system')
  if (updatedBy === currentUserId) return t('extraction.detail.audit.you')
  return `${updatedBy.slice(0, 8)}…`
}

function formatValue(value: string | null): string {
  return value && value.trim() ? value : '-'
}

function diffExtractionRows(
  current: ExtractionRow,
  previous: ExtractionRow | null,
  t: (key: string) => string
): string {
  if (!previous) return '—'

  const changes: string[] = []
  const push = (label: string, prevValue: string | null, nextValue: string | null) => {
    const prev = formatValue(prevValue)
    const next = formatValue(nextValue)
    if (prev !== next) changes.push(`${label}: ${prev} → ${next}`)
  }

  push(t('extraction.fields.status'), previous.status, current.status)
  push(t('common.fields.serialNumber'), previous.serial_number, current.serial_number)
  push(t('common.fields.metal'), previous.metal, current.metal)
  push(t('common.fields.weight'), previous.weight, current.weight)
  push(t('extraction.fields.weightUnit'), previous.weight_unit, current.weight_unit)
  push(t('common.fields.purity'), previous.fineness, current.fineness)
  push(t('common.fields.manufacturer'), previous.producer, current.producer)

  const prevError = previous.error ? previous.error : null
  const nextError = current.error ? current.error : null
  push(t('extraction.fields.error'), prevError, nextError)

  if (changes.length === 0) return '—'
  return changes.join(' · ')
}

export type ExtractionHistoryTableProps = {
  history: ExtractionRow[]
  currentUserId: string
  language: string
  t: (key: string) => string
}

export function ExtractionHistoryTable(props: ExtractionHistoryTableProps) {
  const { history, currentUserId, language, t } = props

  return (
    <div className="mt-6">
      <h4 className="text-body font-bold mb-2">{t('extraction.detail.history')}</h4>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="text-left">
            <tr className="table-divider-strong">
              <th className="py-2 pr-4 whitespace-nowrap w-[11.5rem]">{t('extraction.detail.audit.when')}</th>
              <th className="py-2 pr-4 whitespace-nowrap w-[6.5rem]">{t('extraction.detail.audit.by')}</th>
              <th className="py-2 w-full">{t('extraction.detail.audit.changes')}</th>
            </tr>
          </thead>
          <tbody>
            {history.map((v, index) => (
              <tr key={v.id} className="table-divider">
                <td className="py-2 pr-4 whitespace-nowrap">{formatDateTimeShort(v.created_at, language)}</td>
                <td className="py-2 pr-4 whitespace-nowrap">{formatActor(v.updated_by, currentUserId, t)}</td>
                <td className="py-2">{diffExtractionRows(v, history[index + 1] ?? null, t)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
