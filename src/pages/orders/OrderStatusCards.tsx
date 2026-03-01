import type { ReactNode } from 'react'
import type { OrderStatus } from '../../services/core/order/types'
import {
  StatIconCorrected,
  StatIconError,
  StatIconPending,
  StatIconRejected,
  StatIconTotal,
  StatIconValidated,
} from '../../components/ui/StatCardIcons'
import { StatusCards } from '../../components/ui/StatusCards'

type Counts = {
  pending: number
  validated: number
  corrected: number
  rejected: number
  error: number
  closed: number
}

type Props = {
  counts: Counts | null
  busy: boolean
  activeFilters: OrderStatus[]
  onToggle: (status: OrderStatus) => void
  labels: {
    pending: ReactNode
    validated: ReactNode
    corrected: ReactNode
    rejected: ReactNode
    error: ReactNode
    closed: ReactNode
  }
}

export function OrderStatusCards({ counts, busy, activeFilters, onToggle, labels }: Props) {
  const items = [
    {
      status: 'pending' as const,
      icon: <StatIconPending />,
      label: labels.pending,
      value: counts ? counts.pending : '—',
      valueClassName: 'stat-value-orange',
    },
    {
      status: 'validated' as const,
      icon: <StatIconValidated />,
      label: labels.validated,
      value: counts ? counts.validated : '—',
      valueClassName: 'stat-value-green',
    },
    {
      status: 'corrected' as const,
      icon: <StatIconCorrected />,
      label: labels.corrected,
      value: counts ? counts.corrected : '—',
      valueClassName: 'stat-value-gold',
    },
    {
      status: 'rejected' as const,
      icon: <StatIconRejected />,
      label: labels.rejected,
      value: counts ? counts.rejected : '—',
      valueClassName: 'stat-value-red',
    },
    {
      status: 'error' as const,
      icon: <StatIconError />,
      label: labels.error,
      value: counts ? counts.error : '—',
      valueClassName: 'stat-value-red',
    },
    {
      status: 'closed' as const,
      icon: <StatIconTotal />,
      label: labels.closed,
      value: counts ? counts.closed : '—',
      valueClassName: 'stat-value-gold',
    },
  ]

  return (
    <StatusCards
      items={items}
      activeFilters={activeFilters}
      onToggle={onToggle}
      busy={busy}
      gridClassName="grid grid-cols-1 md:grid-cols-6 gap-4 mb-6"
    />
  )
}
