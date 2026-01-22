import type { TFunction } from 'i18next'

type Props = {
  selectedCount: number
  eligibleCount: number
  busy: boolean
  onReject: () => void
  onClear: () => void
  t: TFunction
}

export function BulkActionsBar({ selectedCount, eligibleCount, busy, onReject, onClear, t }: Props) {
  if (selectedCount === 0) return null

  return (
    <div className="mb-2 flex flex-wrap items-center justify-between gap-3 rounded-md border border-[color:var(--bg-card-border)] bg-white/35 px-3 py-2 dark:bg-white/5">
      <div className="flex items-center gap-2">
        <button type="button" className="btn btn-outline" onClick={onReject} disabled={busy || eligibleCount === 0}>
          {t('common.action.rejectSelected', { count: selectedCount })}
        </button>
      </div>

      <div className="flex items-center">
        <button type="button" className="btn btn-outline" onClick={onClear} disabled={busy}>
          {t('common.action.clearSelection')}
        </button>
      </div>
    </div>
  )
}
