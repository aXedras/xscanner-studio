import { formatDateTimeShort } from '../../lib/utils/date'
import { formatHistoryActor } from './historyTableFormatting'

type HistoryTableRow = {
  id: string | number
  created_at: string
  updated_by: string | null
}

type AuditHistoryTableProps<T extends HistoryTableRow> = {
  history: T[]
  currentUserId: string
  language: string
  t: (key: string) => string
  title?: string
  getChanges: (current: T, previous: T | null) => string
}

export function AuditHistoryTable<T extends HistoryTableRow>({
  history,
  currentUserId,
  language,
  t,
  title,
  getChanges,
}: AuditHistoryTableProps<T>) {
  return (
    <div>
      {title ? <h3 className="text-body font-bold mb-3">{title}</h3> : null}
      {history.length === 0 ? (
        <div className="text-sm text-[color:var(--text-secondary)]">{t('order.detail.historyEmpty')}</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="text-left">
              <tr className="table-divider-strong">
                <th className="py-2 pr-4 whitespace-nowrap w-[11.5rem]">{t('order.detail.audit.when')}</th>
                <th className="py-2 pr-4 whitespace-nowrap w-[6.5rem]">{t('order.detail.audit.by')}</th>
                <th className="py-2 w-full">{t('order.detail.audit.changes')}</th>
              </tr>
            </thead>
            <tbody>
              {history.map((entry, index) => (
                <tr key={entry.id} className="table-divider">
                  <td className="py-2 pr-4 whitespace-nowrap">{formatDateTimeShort(entry.created_at, language)}</td>
                  <td className="py-2 pr-4 whitespace-nowrap">
                    {formatHistoryActor(entry.updated_by, currentUserId, t)}
                  </td>
                  <td className="py-2">{getChanges(entry, history[index + 1] ?? null)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
