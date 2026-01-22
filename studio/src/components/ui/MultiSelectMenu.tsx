import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'

export type MultiSelectMenuOption<Value extends string> = {
  value: Value
  label: string
}

type Props<Value extends string> = {
  label: string
  selected: Value[]
  options: Array<MultiSelectMenuOption<Value>>
  placeholder?: string
  renderSelected?: (input: {
    selected: Value[]
    optionsByValue: Map<Value, MultiSelectMenuOption<Value>>
    placeholder: string
  }) => ReactNode
  onChange: (next: Value[]) => void
}

function CaretDownIcon() {
  return (
    <svg aria-hidden="true" className="h-4 w-4" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function MultiSelectMenu<Value extends string>({
  label,
  selected,
  options,
  placeholder = '—',
  renderSelected,
  onChange,
}: Props<Value>) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement | null>(null)

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

  const { optionsByValue, selectedLabels } = useMemo(() => {
    const nextOptionsByValue = new Map(options.map(o => [o.value, o] as const))
    const nextSelectedLabels = selected.map(value => nextOptionsByValue.get(value)?.label).filter(Boolean) as string[]
    return { optionsByValue: nextOptionsByValue, selectedLabels: nextSelectedLabels }
  }, [options, selected])

  const selectionLabelText = useMemo(() => {
    if (selected.length === 0) return placeholder

    if (selectedLabels.length <= 2) return selectedLabels.join(', ')

    return selectedLabels.join(', ')
  }, [placeholder, selected.length, selectedLabels])

  const title = `${label}: ${selected.length === 0 ? placeholder : selectionLabelText}`

  const selectionLabelNode = useMemo(() => {
    if (!renderSelected) return selectionLabelText
    return renderSelected({ selected, optionsByValue, placeholder })
  }, [optionsByValue, placeholder, renderSelected, selected, selectionLabelText])

  const toggleValue = (value: Value) => {
    if (selected.includes(value)) {
      onChange(selected.filter(v => v !== value))
      return
    }

    onChange([...selected, value])
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
        <span className="flex min-w-0 flex-1 flex-wrap items-center gap-2">
          {typeof selectionLabelNode === 'string' ? (
            <span className="truncate">{selectionLabelNode}</span>
          ) : (
            selectionLabelNode
          )}
        </span>
        <span className="flex-none">
          <CaretDownIcon />
        </span>
      </button>

      {open ? (
        <div className="absolute left-0 right-0 z-50 mt-2 rounded-md border border-slate-200/60 bg-white p-1 shadow-lg dark:border-white/10 dark:bg-slate-950">
          <button
            type="button"
            className="flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm hover:bg-slate-100/60 dark:hover:bg-white/10"
            disabled={selected.length === 0}
            onClick={() => onChange([])}
          >
            <span>—</span>
            {selected.length === 0 ? <span aria-hidden="true">✓</span> : null}
          </button>

          <div className="my-1 h-px bg-slate-200/60 dark:bg-white/10" />

          {options.map(option => (
            <button
              key={option.value}
              type="button"
              className={`flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm hover:bg-slate-100/60 dark:hover:bg-white/10 ${
                selected.includes(option.value) ? 'font-semibold' : ''
              }`.trim()}
              onClick={() => toggleValue(option.value)}
            >
              <span>{option.label}</span>
              {selected.includes(option.value) ? <span aria-hidden="true">✓</span> : null}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  )
}
