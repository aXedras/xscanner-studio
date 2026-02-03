import { getOrderStatusLabelKey, type OrderStatus } from '../../services/core/order/types'

type Translator = (key: string, options?: Record<string, unknown>) => string

type Props = {
  status: OrderStatus
  t: Translator
}

function statusBadgeClass(status: OrderStatus): string {
  switch (status) {
    case 'validated':
      return 'border-emerald-500/40 text-emerald-800 dark:text-emerald-300 bg-emerald-500/10'
    case 'corrected':
      return 'border-sky-500/40 text-sky-800 dark:text-sky-300 bg-sky-500/10'
    case 'closed':
      return 'border-slate-500/40 text-slate-800 dark:text-slate-300 bg-slate-500/10'
    case 'rejected':
    case 'error':
      return 'border-red-500/40 text-red-800 dark:text-red-300 bg-red-500/10'
    case 'pending':
    default:
      return 'border-[rgb(var(--color-gold-rgb)/0.75)] text-[color:var(--color-gold)] bg-[rgb(var(--color-gold-rgb)/0.18)] dark:border-[rgb(var(--color-gold-rgb)/0.55)] dark:text-[color:var(--color-gold-dark)] dark:bg-[rgb(var(--color-gold-rgb)/0.12)]'
  }
}

export function OrderStatusBadge({ status, t }: Props) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold ${statusBadgeClass(status)}`}
    >
      {t(getOrderStatusLabelKey(status))}
    </span>
  )
}
