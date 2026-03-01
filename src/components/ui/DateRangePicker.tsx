import { useEffect, useMemo, useRef, useState } from 'react'
import type { DateRangeSpec } from '../../services/shared/persistence/query'
import { startOfUtcMonth } from './DateRangePickerCalendar'
import { DateRangePickerCalendarView } from './DateRangePickerCalendarView'
import { CalendarRangeIcon, CaretDownIcon } from './DateRangePickerIcons'
import {
  formatIsoDateShort,
  formatLocaleDateInput,
  getLocaleDateInputPlaceholder,
  parseIsoDateString,
  parseLocaleDateInput,
} from '../../lib/utils/date'

type Props = {
  label: string
  value: DateRangeSpec
  fromLabel: string
  toLabel: string
  resetLabel: string
  language: string
  placeholder?: string
  onChange: (next: DateRangeSpec) => void
}

export function DateRangePicker({
  label,
  value,
  fromLabel,
  toLabel,
  resetLabel,
  language,
  placeholder = '—',
  onChange,
}: Props) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement | null>(null)
  const [visibleMonth, setVisibleMonth] = useState<Date>(() => startOfUtcMonth(new Date()))

  const [fromText, setFromText] = useState(() => formatLocaleDateInput(value.from, language))
  const [toText, setToText] = useState(() => formatLocaleDateInput(value.to, language))

  useEffect(() => {
    setFromText(formatLocaleDateInput(value.from, language))
  }, [language, value.from])

  useEffect(() => {
    setToText(formatLocaleDateInput(value.to, language))
  }, [language, value.to])

  useEffect(() => {
    if (!open) return

    const onPointerDown = (event: PointerEvent) => {
      const target = event.target as Node | null
      if (!target) return
      if (!rootRef.current?.contains(target)) setOpen(false)
    }

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false)
    }

    window.addEventListener('pointerdown', onPointerDown)
    window.addEventListener('keydown', onKeyDown)

    return () => {
      window.removeEventListener('pointerdown', onPointerDown)
      window.removeEventListener('keydown', onKeyDown)
    }
  }, [open])

  useEffect(() => {
    if (!open) return
    const fromDate = value.from ? parseIsoDateString(value.from) : null
    const toDate = value.to ? parseIsoDateString(value.to) : null
    const anchor = fromDate ?? toDate ?? new Date()
    setVisibleMonth(startOfUtcMonth(anchor instanceof Date ? anchor : new Date()))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  const buttonLabel = useMemo(() => {
    const from = value.from?.trim()
    const to = value.to?.trim()

    const fromDisplay = from ? formatIsoDateShort(from, language, from) : ''
    const toDisplay = to ? formatIsoDateShort(to, language, to) : ''

    if (!from && !to) return placeholder
    if (from && !to) return `${fromLabel}: ${fromDisplay}`
    if (!from && to) return `${toLabel}: ${toDisplay}`
    return `${fromDisplay} – ${toDisplay}`
  }, [fromLabel, language, placeholder, toLabel, value.from, value.to])

  const title = `${label}: ${buttonLabel}`

  const fromIso = value.from?.trim() || undefined
  const toIso = value.to?.trim() || undefined

  const onPickDay = (iso: string) => {
    if (!fromIso || (fromIso && toIso)) {
      onChange({ ...value, from: iso, to: undefined })
      return
    }

    // from exists and to does not.
    if (iso < fromIso) {
      onChange({ ...value, from: iso, to: fromIso })
      return
    }
    onChange({ ...value, to: iso })
  }

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        className="btn btn-outline w-full"
        aria-label={title}
        title={title}
        onClick={() => setOpen(current => !current)}
      >
        <span className="flex min-w-0 flex-1 items-center gap-2">
          <CalendarRangeIcon />
          <span className="truncate">{buttonLabel}</span>
        </span>
        <span className="flex-none">
          <CaretDownIcon />
        </span>
      </button>

      {open ? (
        <div className="absolute left-0 right-0 z-50 mt-2 rounded-md border border-slate-200/60 bg-white p-3 shadow-lg dark:border-white/10 dark:bg-slate-950">
          <div className="grid grid-cols-1 gap-3">
            <DateRangePickerCalendarView
              visibleMonth={visibleMonth}
              language={language}
              fromIso={fromIso}
              toIso={toIso}
              onVisibleMonthChange={setVisibleMonth}
              onPickDay={onPickDay}
            />

            <label className="block">
              <div className="text-label mb-1">{fromLabel}</div>
              <input
                type="text"
                className="input"
                placeholder={getLocaleDateInputPlaceholder(language)}
                inputMode="numeric"
                value={fromText}
                onChange={e => {
                  const nextText = e.target.value
                  setFromText(nextText)

                  if (!nextText.trim()) {
                    onChange({ ...value, from: undefined })
                    return
                  }

                  const nextIso = parseLocaleDateInput(nextText, language)
                  if (nextIso) onChange({ ...value, from: nextIso })
                }}
              />
            </label>

            <label className="block">
              <div className="text-label mb-1">{toLabel}</div>
              <input
                type="text"
                className="input"
                placeholder={getLocaleDateInputPlaceholder(language)}
                inputMode="numeric"
                value={toText}
                onChange={e => {
                  const nextText = e.target.value
                  setToText(nextText)

                  if (!nextText.trim()) {
                    onChange({ ...value, to: undefined })
                    return
                  }

                  const nextIso = parseLocaleDateInput(nextText, language)
                  if (nextIso) onChange({ ...value, to: nextIso })
                }}
              />
            </label>

            <div className="flex justify-end">
              <button
                type="button"
                className="btn btn-outline"
                disabled={!value.from && !value.to}
                onClick={() => {
                  onChange({})
                  setOpen(false)
                }}
              >
                {resetLabel}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}
