import type { ReactNode } from 'react'

type Props = {
  confidence: number | null | undefined
  label?: string
  showLabel?: boolean
  empty?: ReactNode
  className?: string
}

function toPercentValue(confidence: number): number {
  const value = confidence <= 1 ? confidence * 100 : confidence
  return Math.max(0, Math.min(100, value))
}

function toPercent(confidence: number): string {
  return `${Math.round(toPercentValue(confidence))}%`
}

function confidenceBadgeClass(percent: number): string {
  if (percent >= 83) return 'border-emerald-500/40 text-emerald-800 dark:text-emerald-300 bg-emerald-500/10'
  if (percent >= 65) return 'border-orange-500/40 text-orange-800 dark:text-orange-300 bg-orange-500/10'
  return 'border-red-500/40 text-red-800 dark:text-red-300 bg-red-500/10'
}

export function ConfidenceBadge({ confidence, label, showLabel = false, empty = null, className }: Props) {
  if (typeof confidence !== 'number' || Number.isNaN(confidence)) {
    return empty
  }

  const percent = toPercentValue(confidence)
  const text = toPercent(confidence)

  return (
    <span
      className={
        className ??
        `inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold ${confidenceBadgeClass(
          percent
        )}`
      }
    >
      {showLabel && label ? `${label}: ` : null}
      {text}
    </span>
  )
}
