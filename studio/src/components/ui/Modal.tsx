import type { ReactNode } from 'react'
import { useEffect } from 'react'
import { createPortal } from 'react-dom'

export type ModalProps = {
  open: boolean
  title?: ReactNode
  onClose: () => void
  closeLabel: string
  children: ReactNode
  footer?: ReactNode
  widthClassName?: string
}

export function Modal(props: ModalProps) {
  const { open, title, onClose, closeLabel, children, footer, widthClassName } = props

  useEffect(() => {
    if (!open) return

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }

    window.addEventListener('keydown', onKeyDown)

    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'

    return () => {
      window.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = previousOverflow
    }
  }, [open, onClose])

  if (!open) return null

  return createPortal(
    <div className="fixed inset-0 z-50">
      <div
        className="absolute inset-0 bg-black/40 dark:bg-black/65 backdrop-blur-sm"
        onMouseDown={e => {
          if (e.target === e.currentTarget) onClose()
        }}
      />

      <div className="absolute inset-0 flex items-center justify-center p-4">
        <div
          className={`w-full ${widthClassName ?? 'max-w-5xl'} rounded-2xl border border-[color:var(--bg-card-border)] bg-[color:var(--bg-card)] dark:bg-[rgba(26,26,26,0.96)] text-[color:var(--text-primary)] shadow-2xl overflow-hidden`}
          onMouseDown={e => e.stopPropagation()}
        >
          <div className="px-5 py-4 border-b border-[color:var(--bg-card-border)] flex items-start justify-between gap-4">
            <div className="min-w-0">{title ? <div className="text-body font-bold truncate">{title}</div> : null}</div>
            <button type="button" className="btn btn-outline" onClick={onClose}>
              {closeLabel}
            </button>
          </div>

          <div className="px-5 py-4 max-h-[80vh] overflow-auto">{children}</div>

          {footer ? <div className="px-5 py-4 border-t border-[color:var(--bg-card-border)]">{footer}</div> : null}
        </div>
      </div>
    </div>,
    document.body
  )
}
