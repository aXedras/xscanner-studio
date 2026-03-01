import type { ReactNode } from 'react'
import { useContextSensitiveBack } from '../../lib/router/useContextSensitiveBack'

type Props = {
  title: ReactNode
  subtitle?: ReactNode
  right?: ReactNode
  showBack?: boolean
  backLabel: string
}

export function PageHeader({ title, subtitle, right, showBack = true, backLabel }: Props) {
  const goBack = useContextSensitiveBack('/')

  return (
    <div className="flex items-start justify-between gap-4 mb-6">
      <div className="flex items-start gap-3 min-w-0">
        {showBack ? (
          <button type="button" className="btn btn-icon btn-outline mt-1" aria-label={backLabel} onClick={goBack}>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
        ) : null}

        <div className="min-w-0">
          <h1 className="text-heading text-heading-gold mb-1 truncate">{title}</h1>
          {subtitle ? <p className="text-subtitle">{subtitle}</p> : null}
        </div>
      </div>

      {right ? <div className="flex gap-2">{right}</div> : null}
    </div>
  )
}
