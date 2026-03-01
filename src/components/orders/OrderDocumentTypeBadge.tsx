import { getOrderDocumentTypeLabelKey, type OrderDocumentType } from '../../services/core/order/types'

type Translator = (key: string, options?: Record<string, unknown>) => string

type Props = {
  documentType: OrderDocumentType
  t: Translator
}

function documentTypeBadgeClass(documentType: OrderDocumentType): string {
  switch (documentType) {
    case 'invoice':
      return 'border-sky-500/40 text-sky-800 dark:text-sky-300 bg-sky-500/10'
    case 'order_confirmation':
      return 'border-violet-500/40 text-violet-800 dark:text-violet-300 bg-violet-500/10'
    case 'delivery_note':
      return 'border-emerald-500/40 text-emerald-800 dark:text-emerald-300 bg-emerald-500/10'
    case 'unknown':
    default:
      return 'border-slate-500/40 text-slate-800 dark:text-slate-300 bg-slate-500/10'
  }
}

export function OrderDocumentTypeBadge({ documentType, t }: Props) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold ${documentTypeBadgeClass(
        documentType
      )}`}
    >
      {t(getOrderDocumentTypeLabelKey(documentType))}
    </span>
  )
}
