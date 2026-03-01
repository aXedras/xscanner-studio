import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import type { DataTablePagination } from './DataTableTypes'

function ChevronLeftIcon() {
  return (
    <svg aria-hidden="true" className="h-4 w-4" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M15 18l-6-6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function ChevronRightIcon() {
  return (
    <svg aria-hidden="true" className="h-4 w-4" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M9 6l6 6-6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function RowsPerPageIcon() {
  return (
    <svg aria-hidden="true" className="h-4 w-4" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M4 7h16M4 12h16M4 17h10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <path d="M19 16l2 2 2-2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

type RowsPerPageMenuProps = {
  label: string
  value: number
  options: number[]
  onChange: (value: number) => void
}

function RowsPerPageMenu({ label, value, options, onChange }: RowsPerPageMenuProps) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!open) return

    const onPointerDown = (event: PointerEvent) => {
      const target = event.target as Node | null
      if (!target) return
      if (!rootRef.current?.contains(target)) {
        setOpen(false)
      }
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

  const title = `${label}: ${value}`

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        className="btn btn-outline btn-icon"
        aria-label={title}
        title={title}
        onClick={() => setOpen(current => !current)}
      >
        <RowsPerPageIcon />
      </button>

      {open ? (
        <div className="absolute right-0 z-50 mt-2 w-28 rounded-md border border-slate-200/60 bg-white p-1 shadow-lg dark:border-white/10 dark:bg-slate-950">
          {options.map(size => (
            <button
              key={size}
              type="button"
              className={`flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm hover:bg-slate-100/60 dark:hover:bg-white/10 ${
                size === value ? 'font-semibold' : ''
              }`.trim()}
              onClick={() => {
                onChange(size)
                setOpen(false)
              }}
            >
              <span>{size}</span>
              {size === value ? <span aria-hidden="true">✓</span> : null}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  )
}

type PageIndicatorProps = {
  label: string
  page: number
  totalPages: number
}

function PageIndicator({ label, page, totalPages }: PageIndicatorProps) {
  const [width, setWidth] = useState<number | undefined>(undefined)
  const measureRef = useRef<HTMLSpanElement | null>(null)

  const maxDigits = String(totalPages).length
  const measureText = `${label} ${'9'.repeat(maxDigits)} / ${'9'.repeat(maxDigits)}`

  useLayoutEffect(() => {
    const el = measureRef.current
    if (!el) return

    const nextWidth = Math.ceil(el.getBoundingClientRect().width) + 2
    setWidth(nextWidth)
  }, [measureText])

  useEffect(() => {
    const onResize = () => {
      const el = measureRef.current
      if (!el) return
      const nextWidth = Math.ceil(el.getBoundingClientRect().width) + 2
      setWidth(nextWidth)
    }

    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  return (
    <span className="relative inline-flex justify-center">
      <span ref={measureRef} className="pointer-events-none absolute left-0 top-0 invisible whitespace-nowrap text-xs">
        {measureText}
      </span>
      <span
        className="inline-block whitespace-nowrap text-center text-xs text-[color:var(--text-secondary)]"
        style={width ? { width } : undefined}
      >
        {label} {page} / {totalPages}
      </span>
    </span>
  )
}

type Props = {
  pagination: DataTablePagination
  totalPages: number
}

export function DataTablePaginationControls({ pagination, totalPages }: Props) {
  return (
    <div className="flex items-center justify-end gap-2">
      <RowsPerPageMenu
        label={pagination.labelRowsPerPage}
        value={pagination.pageSize}
        options={pagination.pageSizeOptions ?? [10, 20, 50, 100]}
        onChange={pagination.onPageSizeChange}
      />

      <div className="flex items-center gap-2">
        <button
          type="button"
          className="btn btn-outline btn-icon"
          disabled={pagination.page <= 1}
          aria-label={pagination.labelPrev}
          title={pagination.labelPrev}
          onClick={() => pagination.onPageChange(Math.max(1, pagination.page - 1))}
        >
          <ChevronLeftIcon />
        </button>

        <PageIndicator label={pagination.labelPage} page={pagination.page} totalPages={totalPages} />

        <button
          type="button"
          className="btn btn-outline btn-icon"
          disabled={pagination.page >= totalPages}
          aria-label={pagination.labelNext}
          title={pagination.labelNext}
          onClick={() => pagination.onPageChange(Math.min(totalPages, pagination.page + 1))}
        >
          <ChevronRightIcon />
        </button>
      </div>
    </div>
  )
}
