import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

type Props = {
  label: string
  to?: string
  onClick?: () => void
  inactive?: boolean
  className?: string
  children: ReactNode
}

export function ActionIconButton({ label, to, onClick, inactive = false, className, children }: Props) {
  const baseClassName =
    `btn btn-outline btn-icon btn-sm text-[18px] ${inactive ? 'btn-inactive' : ''} ${className ?? ''}`.trim()
  const title = inactive ? undefined : label

  if (to) {
    if (inactive) {
      return (
        <span className={baseClassName} aria-disabled="true" title={title}>
          {children}
        </span>
      )
    }

    return (
      <Link to={to} className={baseClassName} aria-label={label} title={title}>
        {children}
      </Link>
    )
  }

  return (
    <button
      type="button"
      className={baseClassName}
      aria-label={label}
      title={title}
      onClick={inactive ? undefined : onClick}
      disabled={inactive}
    >
      {children}
    </button>
  )
}
