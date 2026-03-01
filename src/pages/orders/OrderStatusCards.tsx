import type { ReactNode } from 'react'
import type { OrderStatus } from '../../services/core/order/types'
import { InlineSpinner } from '../../components/ui/InlineSpinner'
import {
  StatIconCorrected,
  StatIconError,
  StatIconPending,
  StatIconRejected,
  StatIconTotal,
  StatIconValidated,
} from '../../components/ui/StatCardIcons'

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

function Card({
  active,
  onClick,
  icon,
  label,
  value,
  valueClassName,
  busy,
}: {
  active: boolean
  onClick: () => void
  icon: ReactNode
  label: ReactNode
  value: ReactNode
  valueClassName: string
  busy: boolean
}) {
  return (
    <button
      type="button"
      className={`stat-card text-left ${active ? 'ring-2 ring-[rgb(var(--color-gold-rgb)/0.60)]' : ''}`}
      onClick={onClick}
    >
      {icon}
      <div className="stat-content">
        <p className="stat-label flex items-center gap-2">
          {label}
          {busy ? (
            <span className="text-[color:var(--text-secondary)]">
              <InlineSpinner size={14} />
            </span>
          ) : null}
        </p>
        <p className={`stat-value ${valueClassName}`.trim()}>{value}</p>
      </div>
    </button>
  )
}

export function OrderStatusCards({ counts, busy, activeFilters, onToggle, labels }: Props) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-6 gap-4 mb-6">
      <Card
        active={activeFilters.includes('pending')}
        onClick={() => onToggle('pending')}
        icon={<StatIconPending />}
        label={labels.pending}
        value={counts ? counts.pending : '—'}
        valueClassName="stat-value-orange"
        busy={busy}
      />
      <Card
        active={activeFilters.includes('validated')}
        onClick={() => onToggle('validated')}
        icon={<StatIconValidated />}
        label={labels.validated}
        value={counts ? counts.validated : '—'}
        valueClassName="stat-value-green"
        busy={busy}
      />
      <Card
        active={activeFilters.includes('corrected')}
        onClick={() => onToggle('corrected')}
        icon={<StatIconCorrected />}
        label={labels.corrected}
        value={counts ? counts.corrected : '—'}
        valueClassName="stat-value-gold"
        busy={busy}
      />
      <Card
        active={activeFilters.includes('rejected')}
        onClick={() => onToggle('rejected')}
        icon={<StatIconRejected />}
        label={labels.rejected}
        value={counts ? counts.rejected : '—'}
        valueClassName="stat-value-red"
        busy={busy}
      />
      <Card
        active={activeFilters.includes('error')}
        onClick={() => onToggle('error')}
        icon={<StatIconError />}
        label={labels.error}
        value={counts ? counts.error : '—'}
        valueClassName="stat-value-red"
        busy={busy}
      />
      <Card
        active={activeFilters.includes('closed')}
        onClick={() => onToggle('closed')}
        icon={<StatIconTotal />}
        label={labels.closed}
        value={counts ? counts.closed : '—'}
        valueClassName="stat-value-gold"
        busy={busy}
      />
    </div>
  )
}
