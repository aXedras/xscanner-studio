import type { ReactNode } from 'react'
import { InlineSpinner } from './InlineSpinner'

export type StatusCardItem<TStatus extends string> = {
  status: TStatus
  icon: ReactNode
  label: ReactNode
  value: ReactNode
  valueClassName: string
}

type StatusCardsProps<TStatus extends string> = {
  items: StatusCardItem<TStatus>[]
  activeFilters: TStatus[]
  onToggle: (status: TStatus) => void
  busy: boolean
  gridClassName: string
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

export function StatusCards<TStatus extends string>({
  items,
  activeFilters,
  onToggle,
  busy,
  gridClassName,
}: StatusCardsProps<TStatus>) {
  return (
    <div className={gridClassName}>
      {items.map(item => (
        <Card
          key={item.status}
          active={activeFilters.includes(item.status)}
          onClick={() => onToggle(item.status)}
          icon={item.icon}
          label={item.label}
          value={item.value}
          valueClassName={item.valueClassName}
          busy={busy}
        />
      ))}
    </div>
  )
}
