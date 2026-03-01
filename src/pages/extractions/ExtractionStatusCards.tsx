import type { ReactNode } from 'react'
import type { ExtractionStatus } from '../../services/core/extraction/types'
import {
  StatIconCorrected,
  StatIconError,
  StatIconPending,
  StatIconRejected,
  StatIconValidated,
} from '../../components/ui/StatCardIcons'
import { StatusCards } from '../../components/ui/StatusCards'

type Counts = {
  pending: number
  corrected: number
  validated: number
  rejected: number
  error: number
}

type Props = {
  counts: Counts | null
  busy: boolean
  activeFilters: ExtractionStatus[]
  onToggle: (status: ExtractionStatus) => void
  labels: {
    pending: ReactNode
    corrected: ReactNode
    validated: ReactNode
    rejected: ReactNode
    error: ReactNode
  }
}

export function ExtractionStatusCards({ counts, busy, activeFilters, onToggle, labels }: Props) {
  const items = [
    {
      status: 'pending' as const,
      icon: <StatIconPending />,
      label: labels.pending,
      value: counts ? counts.pending : '—',
      valueClassName: 'stat-value-orange',
    },
    {
      status: 'corrected' as const,
      icon: <StatIconCorrected />,
      label: labels.corrected,
      value: counts ? counts.corrected : '—',
      valueClassName: 'stat-value-gold',
    },
    {
      status: 'validated' as const,
      icon: <StatIconValidated />,
      label: labels.validated,
      value: counts ? counts.validated : '—',
      valueClassName: 'stat-value-green',
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
  ]

  return (
    <StatusCards
      items={items}
      activeFilters={activeFilters}
      onToggle={onToggle}
      busy={busy}
      gridClassName="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6"
    />
  )
}
