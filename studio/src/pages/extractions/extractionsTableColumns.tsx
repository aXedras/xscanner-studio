import type { RefObject } from 'react'
import type { TFunction } from 'i18next'
import { DetailsIcon, RegisterIcon, RejectIcon } from '../../components/ui/ActionIcons'
import { ActionIconButton } from '../../components/ui/ActionIconButton'
import { ExtractionStatusBadge } from '../../components/extractions/ExtractionStatusBadge'
import { ConfidenceBadge } from '../../components/extractions/ConfidenceBadge'
import type { DataTableColumn } from '../../components/tables/DataTable'
import { formatDateTimeShort } from '../../lib/utils/date'
import type { ExtractionListSortField, ExtractionRow, ExtractionStatus } from '../../services/core/extraction/types'

type Args = {
  t: TFunction
  language: string

  selected: Set<string>
  busyIds: Set<string>
  bulkBusy: boolean
  multiSelectActive: boolean

  selectableIdsOnPage: string[]
  allSelectedOnPage: boolean

  headerCheckboxRef: RefObject<HTMLInputElement>
  onToggleAllOnPage: () => void
  onToggleRow: (id: string) => void

  onRegister: (originalId: string) => void
  onReject: (originalId: string) => void
}

function isFinalStatus(status: ExtractionStatus): boolean {
  return status === 'validated' || status === 'rejected'
}

export function createExtractionsTableColumns({
  t,
  language,
  selected,
  busyIds,
  bulkBusy,
  multiSelectActive,
  selectableIdsOnPage,
  allSelectedOnPage,
  headerCheckboxRef,
  onToggleAllOnPage,
  onToggleRow,
  onRegister,
  onReject,
}: Args): Array<DataTableColumn<ExtractionRow, ExtractionListSortField>> {
  const selectColumn: DataTableColumn<ExtractionRow, ExtractionListSortField> = {
    key: 'select',
    header: (
      <input
        ref={headerCheckboxRef}
        type="checkbox"
        className="h-4 w-4"
        aria-label={t('common.table.selectAll')}
        checked={allSelectedOnPage}
        disabled={selectableIdsOnPage.length === 0 || bulkBusy}
        onChange={onToggleAllOnPage}
      />
    ),
    headerClassName: 'w-10 pr-2',
    cellClassName: 'w-10 pr-2',
    cell: row => {
      const id = String(row.original_id)
      const disabled = isFinalStatus(row.status) || busyIds.has(id) || bulkBusy
      return (
        <input
          type="checkbox"
          className="h-4 w-4"
          aria-label={t('common.table.selectRow')}
          checked={selected.has(id)}
          disabled={disabled}
          onChange={() => onToggleRow(id)}
        />
      )
    },
  }

  return [
    selectColumn,
    {
      key: 'created_at',
      header: t('common.fields.createdAt'),
      sortField: 'created_at',
      cell: row => <span className="whitespace-nowrap">{formatDateTimeShort(row.created_at, language)}</span>,
    },
    {
      key: 'status',
      header: t('extraction.fields.status'),
      sortField: 'status',
      cell: row => <ExtractionStatusBadge status={row.status} t={t} />,
    },
    {
      key: 'serial_number',
      header: t('common.fields.serialNumber'),
      sortField: 'serial_number',
      cell: row => row.serial_number ?? '-',
    },
    {
      key: 'metal',
      header: t('common.fields.metal'),
      sortField: 'metal',
      cell: row => row.metal ?? '-',
    },
    {
      key: 'producer',
      header: t('common.fields.manufacturer'),
      sortField: 'producer',
      cell: row => row.producer ?? '-',
    },
    {
      key: 'strategy_used',
      header: t('extraction.fields.strategy'),
      sortField: 'strategy_used',
      cell: row => row.strategy_used,
    },
    {
      key: 'confidence',
      header: t('extraction.fields.confidence'),
      sortField: 'confidence',
      cell: row => <ConfidenceBadge confidence={row.confidence} empty="-" />,
    },
    {
      key: 'action',
      header: '',
      cell: row => {
        const id = String(row.original_id)
        const isFinal = isFinalStatus(row.status)
        const isBusy = busyIds.has(id) || bulkBusy
        const inactive = multiSelectActive || isFinal || isBusy

        return (
          <div className="flex items-center justify-end gap-1">
            <ActionIconButton
              label={t('common.action.showDetails')}
              to={`/extractions/${row.original_id}`}
              inactive={multiSelectActive}
            >
              <DetailsIcon />
            </ActionIconButton>

            <ActionIconButton label={t('common.action.register')} inactive={inactive} onClick={() => onRegister(id)}>
              <RegisterIcon />
            </ActionIconButton>

            <ActionIconButton label={t('common.action.reject')} inactive={inactive} onClick={() => onReject(id)}>
              <RejectIcon />
            </ActionIconButton>
          </div>
        )
      },
    },
  ]
}
