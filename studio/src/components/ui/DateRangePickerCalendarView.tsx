import { useMemo } from 'react'
import { toIntlLocale, toIsoDateString, formatIsoDateShort } from '../../lib/utils/date'
import { addUtcMonths, getDaysInUtcMonth, getUtcWeekdayMondayFirst, startOfUtcMonth } from './DateRangePickerCalendar'
import { ChevronLeftIcon, ChevronRightIcon } from './DateRangePickerIcons'

type Props = {
  visibleMonth: Date
  language: string
  fromIso?: string
  toIso?: string
  onVisibleMonthChange: (next: Date) => void
  onPickDay: (iso: string) => void
}

export function DateRangePickerCalendarView({
  visibleMonth,
  language,
  fromIso,
  toIso,
  onVisibleMonthChange,
  onPickDay,
}: Props) {
  const monthLabel = useMemo(() => {
    const d = startOfUtcMonth(visibleMonth)
    return d.toLocaleString(toIntlLocale(language), { month: 'long', year: 'numeric', timeZone: 'UTC' })
  }, [language, visibleMonth])

  const weekdayLabels = useMemo(() => {
    const locale = toIntlLocale(language)
    const fmt = new Intl.DateTimeFormat(locale, { weekday: 'short', timeZone: 'UTC' })
    return Array.from({ length: 7 }, (_, index) => fmt.format(new Date(Date.UTC(2024, 0, 1 + index))))
  }, [language])

  const monthGrid = useMemo(() => {
    const first = startOfUtcMonth(visibleMonth)
    const offset = getUtcWeekdayMondayFirst(first)
    const daysInMonth = getDaysInUtcMonth(visibleMonth)

    const cells: Array<number | null> = []
    for (let i = 0; i < offset; i += 1) cells.push(null)
    for (let day = 1; day <= daysInMonth; day += 1) cells.push(day)

    while (cells.length % 7 !== 0) cells.push(null)

    const weeks: Array<Array<number | null>> = []
    for (let i = 0; i < cells.length; i += 7) weeks.push(cells.slice(i, i + 7))
    return weeks
  }, [visibleMonth])

  const isInRange = (iso: string): boolean => {
    if (!fromIso && !toIso) return false
    if (fromIso && !toIso) return iso === fromIso
    if (!fromIso && toIso) return iso === toIso

    const a = fromIso!
    const b = toIso!
    const start = a <= b ? a : b
    const end = a <= b ? b : a
    return iso >= start && iso <= end
  }

  const isEdge = (iso: string): { isFrom: boolean; isTo: boolean } => ({
    isFrom: Boolean(fromIso && iso === fromIso),
    isTo: Boolean(toIso && iso === toIso),
  })

  return (
    <div className="rounded-md border border-slate-200/60 p-2 dark:border-white/10">
      <div className="mb-2 flex items-center justify-between">
        <button
          type="button"
          className="btn btn-outline btn-icon"
          aria-label="Previous month"
          title="Previous month"
          onClick={() => onVisibleMonthChange(addUtcMonths(visibleMonth, -1))}
        >
          <ChevronLeftIcon />
        </button>
        <div className="text-sm font-semibold">{monthLabel}</div>
        <button
          type="button"
          className="btn btn-outline btn-icon"
          aria-label="Next month"
          title="Next month"
          onClick={() => onVisibleMonthChange(addUtcMonths(visibleMonth, 1))}
        >
          <ChevronRightIcon />
        </button>
      </div>

      <div className="grid grid-cols-7 gap-1 text-xs text-[color:var(--text-secondary)]">
        {weekdayLabels.map(d => (
          <div key={d} className="py-1 text-center">
            {d}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-7 gap-1">
        {monthGrid.flatMap((week, wIdx) =>
          week.map((day, dIdx) => {
            if (!day) return <div key={`e-${wIdx}-${dIdx}`} className="h-8" />

            const iso = toIsoDateString(
              new Date(Date.UTC(visibleMonth.getUTCFullYear(), visibleMonth.getUTCMonth(), day))
            )
            const inRange = isInRange(iso)
            const { isFrom, isTo } = isEdge(iso)

            const dayLabel = formatIsoDateShort(iso, language, iso)

            const base = 'h-8 w-full rounded-md text-sm'
            const state = inRange
              ? 'bg-[rgb(var(--color-gold-rgb)/0.20)] border border-[rgb(var(--color-gold-rgb)/0.70)] ring-1 ring-[rgb(var(--color-gold-rgb)/0.20)] dark:bg-[rgb(var(--color-gold-rgb)/0.15)] dark:border-[rgb(var(--color-gold-rgb)/0.55)] dark:ring-0'
              : 'hover:bg-slate-100/60 dark:hover:bg-white/10'
            const edge =
              isFrom || isTo
                ? 'font-semibold bg-[rgb(var(--color-gold-rgb)/0.35)] border border-[color:var(--color-gold)] ring-2 ring-[rgb(var(--color-gold-rgb)/0.30)] dark:bg-[rgb(var(--color-gold-rgb)/0.25)] dark:border-[color:var(--color-gold)] dark:ring-2 dark:ring-[rgb(var(--color-gold-rgb)/0.35)]'
                : ''

            return (
              <button
                key={iso}
                type="button"
                className={`${base} ${state} ${edge}`.trim()}
                aria-label={dayLabel}
                title={dayLabel}
                onClick={() => onPickDay(iso)}
              >
                {day}
              </button>
            )
          })
        )}
      </div>
    </div>
  )
}
