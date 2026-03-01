import type { ImageInspectorLabels } from './useImageInspector'
import { useImageInspector } from './useImageInspector'

type Props = {
  src: string
  alt: string
  previewMaxHeight?: number
  labels: ImageInspectorLabels
}

export default function ImageInspector({ src, alt, previewMaxHeight = 420, labels }: Props) {
  const {
    open,
    canPan,
    zoomScale,
    transform,
    previewRef,
    viewportRef,
    imageRef,
    onOpenAtClick,
    onClose,
    onPreviewKeyDown,
    onViewportKeyDown,
    onWheel,
    onPointerDown,
    onPointerMove,
    onPointerUp,
    zoomBy,
    resetView,
    onPreviewImgLoad,
    onZoomImgLoad,
  } = useImageInspector({ src })

  const overlayButtonClass =
    'inline-flex items-center justify-center rounded-md border border-white/20 bg-white/10 px-3 py-1 text-sm font-semibold text-white shadow-sm hover:bg-white/15 focus:outline-none focus-visible:ring-2 focus-visible:ring-white/40 disabled:opacity-50'
  const overlayButtonSmallClass = `${overlayButtonClass} w-9 px-0`
  const overlayPrimaryButtonClass =
    'inline-flex items-center justify-center rounded-md border border-[rgb(var(--color-gold-rgb)/0.60)] bg-[rgb(var(--color-gold-rgb)/0.90)] px-3 py-1 text-sm font-semibold text-[color:var(--bg-app)] shadow-sm hover:bg-[color:var(--color-gold)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[rgb(var(--color-gold-rgb)/0.50)]'

  return (
    <div>
      <div
        className="group relative rounded-lg border overflow-hidden cursor-zoom-in"
        style={{ height: `${previewMaxHeight}px` }}
        role="button"
        tabIndex={0}
        aria-label={labels.inspect}
        onClick={onOpenAtClick}
        onKeyDown={onPreviewKeyDown}
        ref={previewRef}
      >
        <img
          src={src}
          alt={alt}
          className={`w-full h-full object-contain bg-black/5 transition-opacity ${open ? 'opacity-0' : 'opacity-100'}`}
          onLoad={e => {
            const img = e.currentTarget
            onPreviewImgLoad(img)
          }}
        />

        <div
          className={`pointer-events-none absolute inset-0 transition-opacity ${
            open ? 'opacity-0' : 'opacity-0 group-hover:opacity-100'
          }`}
        >
          <div className="absolute inset-0 bg-black/5" />
          <div className="absolute bottom-3 right-3 flex items-center justify-center rounded-full bg-black/55 p-2 text-white">
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              aria-hidden="true"
            >
              <path d="M10.5 18a7.5 7.5 0 1 1 0-15 7.5 7.5 0 0 1 0 15Z" stroke="currentColor" strokeWidth="2" />
              <path d="M16.5 16.5 21 21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              <path d="M10.5 7.5v6M7.5 10.5h6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </div>
        </div>

        {open ? (
          <div className="absolute inset-0 z-50">
            <div className="absolute inset-0 bg-black/35" />

            <div
              ref={viewportRef}
              tabIndex={0}
              className={`absolute inset-0 overflow-hidden rounded-md border border-[color:var(--bg-card-border)] bg-black/20 ${
                canPan ? 'cursor-grab active:cursor-grabbing' : 'cursor-zoom-in'
              }`}
              onWheel={onWheel}
              onKeyDown={onViewportKeyDown}
              onPointerDown={onPointerDown}
              onPointerMove={onPointerMove}
              onPointerUp={onPointerUp}
              onPointerCancel={onPointerUp}
              onClick={e => e.stopPropagation()}
            >
              <img
                ref={imageRef}
                src={src}
                alt={alt}
                draggable={false}
                className="absolute left-1/2 top-1/2 max-w-none select-none"
                style={{ transform: `translate(-50%, -50%) ${transform}`, transformOrigin: 'center' }}
                onLoad={e => {
                  const img = e.currentTarget
                  onZoomImgLoad(img)
                }}
                onClick={e => e.stopPropagation()}
              />

              <div
                className="absolute left-2 right-2 top-2 flex items-center justify-between gap-2 rounded-md border border-white/15 bg-black/70 backdrop-blur px-2 py-1 shadow-lg"
                onClick={e => e.stopPropagation()}
                data-image-inspector-ui
              >
                <div className="text-sm text-white/85">
                  {labels.zoom}: {(zoomScale * 100).toFixed(0)}%
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    className={overlayButtonSmallClass}
                    onClick={e => {
                      e.stopPropagation()
                      zoomBy(-0.25)
                    }}
                    aria-label={labels.zoomOut}
                    title={labels.zoomOut}
                  >
                    −
                  </button>
                  <button
                    type="button"
                    className={overlayButtonSmallClass}
                    onClick={e => {
                      e.stopPropagation()
                      zoomBy(0.25)
                    }}
                    aria-label={labels.zoomIn}
                    title={labels.zoomIn}
                  >
                    +
                  </button>
                  <button
                    type="button"
                    className={overlayButtonClass}
                    onClick={e => {
                      e.stopPropagation()
                      resetView()
                    }}
                  >
                    {labels.reset}
                  </button>
                  <button
                    type="button"
                    className={overlayPrimaryButtonClass}
                    onClick={e => {
                      e.stopPropagation()
                      onClose()
                    }}
                  >
                    {labels.close}
                  </button>
                </div>
              </div>

              <div
                className="absolute left-2 right-2 bottom-2 rounded-md border border-white/15 bg-black/70 backdrop-blur px-2 py-1 text-xs text-white/75 shadow-lg"
                onClick={e => e.stopPropagation()}
                data-image-inspector-ui
              >
                {labels.hint}
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  )
}
