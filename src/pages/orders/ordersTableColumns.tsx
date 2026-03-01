import type { TFunction } from 'i18next'
import type { DataTableColumn } from '../../components/tables/DataTable'
import { ActionIconButton } from '../../components/ui/ActionIconButton'
import { DetailsIcon } from '../../components/ui/ActionIcons'
import { formatDateTimeShort, formatIsoDateShort } from '../../lib/utils/date'
import { formatOrderDocumentNumberForDisplay } from '../../lib/utils/order'
import { OrderStatusBadge } from '../../components/orders/OrderStatusBadge'
import { OrderDocumentTypeBadge } from '../../components/orders/OrderDocumentTypeBadge'
import { ConfidenceBadge } from '../../components/extractions/ConfidenceBadge'
import type { OrderListSortField, OrderRow } from '../../services/core/order/types'

type Args = {
  t: TFunction
  language: string
}

export function createOrdersTableColumns({ t, language }: Args): Array<DataTableColumn<OrderRow, OrderListSortField>> {
  return [
    {
      key: 'created_at',
      header: t('common.fields.createdAt'),
      sortField: 'created_at',
      cell: row => <span className="whitespace-nowrap">{formatDateTimeShort(row.created_at, language)}</span>,
    },
    {
      key: 'status',
      header: t('order.fields.status'),
      sortField: 'status',
      cell: row => <OrderStatusBadge status={row.status} t={t} />,
    },
    {
      key: 'document_issuer',
      header: t('order.fields.documentIssuer'),
      sortField: 'document_issuer',
      cell: row => row.document_issuer,
    },
    {
      key: 'document_type',
      header: t('order.fields.documentType'),
      cell: row => <OrderDocumentTypeBadge documentType={row.document_type} t={t} />,
    },
    {
      key: 'document_number',
      header: t('order.fields.documentNumber'),
      sortField: 'document_number',
      cell: row => (
        <span className="whitespace-nowrap">{formatOrderDocumentNumberForDisplay(row.document_number, t)}</span>
      ),
    },
    {
      key: 'document_date',
      header: t('order.fields.documentDate'),
      sortField: 'document_date',
      cell: row => <span className="whitespace-nowrap">{formatIsoDateShort(row.document_date, language)}</span>,
    },
    {
      key: 'strategy_used',
      header: t('order.fields.strategyUsed'),
      cell: row => row.strategy_used ?? '-',
    },
    {
      key: 'confidence',
      header: t('order.fields.confidence'),
      cell: row => <ConfidenceBadge confidence={row.confidence} empty="-" />,
    },
    {
      key: 'action',
      header: '',
      cell: row => (
        <div className="flex items-center justify-end">
          <ActionIconButton label={t('common.action.showDetails')} to={`/orders/${row.original_id}`}>
            <DetailsIcon />
          </ActionIconButton>
        </div>
      ),
    },
  ]
}
