import type { UiMessageVariant } from '../../ui/messages/types'

type Props = {
  variant: UiMessageVariant
  title?: string
  description: string
  details?: string
  closeLabel: string
  onClose: () => void
}

const getVariantAccentClasses = (variant: UiMessageVariant): string => {
  switch (variant) {
    case 'success':
      return 'border-l-emerald-500'
    case 'warning':
      return 'border-l-amber-500'
    case 'error':
      return 'border-l-red-500'
    case 'info':
    default:
      return 'border-l-slate-400'
  }
}

export default function InfoPanel({ variant, title, description, details, closeLabel, onClose }: Props) {
  return (
    <div
      className={`w-full rounded-md border border-[color:var(--bg-card-border)] border-l-4 bg-[color:var(--bg-card)] p-3 flex items-start gap-3 ${getVariantAccentClasses(
        variant
      )}`}
    >
      <div className="flex-1 min-w-0">
        {title ? <div className="font-semibold leading-snug text-[color:var(--text-primary)]">{title}</div> : null}
        <div className="text-sm leading-snug break-words text-[color:var(--text-secondary)]">{description}</div>

        {details ? (
          <details className="mt-2">
            <summary className="cursor-pointer text-xs text-[color:var(--text-secondary)]">Details</summary>
            <pre className="mt-2 text-xs whitespace-pre-wrap break-words rounded-md border border-[color:var(--bg-card-border)] bg-black/20 p-2 text-[color:var(--text-secondary)]">
              {details}
            </pre>
          </details>
        ) : null}
      </div>

      <button type="button" className="btn btn-icon" aria-label={closeLabel} onClick={onClose}>
        ×
      </button>
    </div>
  )
}
