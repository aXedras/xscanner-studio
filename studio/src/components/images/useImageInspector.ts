import type { KeyboardEvent, MouseEvent, PointerEvent, WheelEvent } from 'react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

export type ImageInspectorLabels = {
  inspect: string
  close: string
  reset: string
  zoomIn: string
  zoomOut: string
  zoom: string
  hint: string
}

type Point = { x: number; y: number }
type Size = { width: number; height: number }

type ViewState = {
  zoomScale: number
  translate: Point
}

type RelativePoint = { x: number; y: number }

const clamp = (value: number, min: number, max: number): number => Math.min(max, Math.max(min, value))

export function useImageInspector(params: { src: string }) {
  const { src } = params

  const [open, setOpen] = useState(false)
  const [baseScale, setBaseScale] = useState(1)
  const [view, setView] = useState<ViewState>({ zoomScale: 1, translate: { x: 0, y: 0 } })
  const [naturalSize, setNaturalSize] = useState<Size | null>(null)
  const [pendingFocus, setPendingFocus] = useState<RelativePoint | null>(null)

  const previewRef = useRef<HTMLDivElement | null>(null)
  const viewportRef = useRef<HTMLDivElement | null>(null)
  const imageRef = useRef<HTMLImageElement | null>(null)
  const dragState = useRef<{ startPointer: Point; startTranslate: Point } | null>(null)

  const zoomScale = view.zoomScale
  const translate = view.translate

  const effectiveScale = baseScale * zoomScale
  const canPan = zoomScale > 1

  const getViewportSize = useCallback((): Size | null => {
    const el = viewportRef.current
    if (!el) return null
    const rect = el.getBoundingClientRect()
    if (!rect.width || !rect.height) return null
    return { width: rect.width, height: rect.height }
  }, [])

  const getMaxTranslate = useCallback(
    (nextZoomScale: number, nextBaseScale: number): Point => {
      const vp = getViewportSize()
      if (!vp || !naturalSize) return { x: 0, y: 0 }

      const scaledWidth = naturalSize.width * nextBaseScale * nextZoomScale
      const scaledHeight = naturalSize.height * nextBaseScale * nextZoomScale

      const maxX = Math.max(0, (scaledWidth - vp.width) / 2)
      const maxY = Math.max(0, (scaledHeight - vp.height) / 2)

      return { x: maxX, y: maxY }
    },
    [getViewportSize, naturalSize]
  )

  const clampTranslate = useCallback(
    (next: Point, nextZoomScale: number, nextBaseScale: number): Point => {
      const max = getMaxTranslate(nextZoomScale, nextBaseScale)
      return {
        x: clamp(next.x, -max.x, max.x),
        y: clamp(next.y, -max.y, max.y),
      }
    },
    [getMaxTranslate]
  )

  const computeBaseScaleValue = useCallback((): number | null => {
    const vp = getViewportSize()
    if (!vp || !naturalSize) return null
    const value = Math.min(1, vp.width / naturalSize.width, vp.height / naturalSize.height)
    return value || 1
  }, [getViewportSize, naturalSize])

  const computeInitialZoomScale = useCallback(
    (nextBaseScale: number): number => {
      const vp = getViewportSize()
      if (!vp || !naturalSize) return 1

      const scaleToFillWidth = vp.width / (naturalSize.width * nextBaseScale)
      return clamp(Number(scaleToFillWidth.toFixed(2)), 1, 6)
    },
    [getViewportSize, naturalSize]
  )

  const resetView = useCallback(() => {
    setView({ zoomScale: 1, translate: { x: 0, y: 0 } })
  }, [])

  const setViewFocusedAt = useCallback(
    (rel: RelativePoint, nextZoomScale: number, nextBaseScale: number) => {
      if (!naturalSize) {
        setView({ zoomScale: nextZoomScale, translate: { x: 0, y: 0 } })
        return
      }

      const px = clamp(rel.x, 0, 1) * naturalSize.width
      const py = clamp(rel.y, 0, 1) * naturalSize.height
      const effective = nextBaseScale * nextZoomScale

      const nextTranslate = {
        x: (naturalSize.width / 2 - px) * effective,
        y: (naturalSize.height / 2 - py) * effective,
      }

      setView({
        zoomScale: nextZoomScale,
        translate: clampTranslate(nextTranslate, nextZoomScale, nextBaseScale),
      })
    },
    [clampTranslate, naturalSize]
  )

  const zoomBy = useCallback(
    (delta: number) => {
      setView(prev => {
        const nextZoomScale = clamp(Number((prev.zoomScale + delta).toFixed(2)), 1, 6)
        return {
          zoomScale: nextZoomScale,
          translate: clampTranslate(prev.translate, nextZoomScale, baseScale),
        }
      })
    },
    [baseScale, clampTranslate]
  )

  const onOpen = useCallback(() => {
    resetView()
    setPendingFocus({ x: 0.5, y: 0.5 })
    setOpen(true)
  }, [resetView])

  const onOpenAtClick = useCallback(
    (e: MouseEvent) => {
      const container = previewRef.current
      if (!container) {
        onOpen()
        return
      }

      const rect = container.getBoundingClientRect()
      const cx = e.clientX - rect.left
      const cy = e.clientY - rect.top

      if (!naturalSize) {
        resetView()
        setPendingFocus({ x: 0.5, y: 0.5 })
        setOpen(true)
        return
      }

      const fit = Math.min(rect.width / naturalSize.width, rect.height / naturalSize.height)
      const renderedW = naturalSize.width * fit
      const renderedH = naturalSize.height * fit
      const offsetX = (rect.width - renderedW) / 2
      const offsetY = (rect.height - renderedH) / 2

      const rel = {
        x: (cx - offsetX) / renderedW,
        y: (cy - offsetY) / renderedH,
      }

      setPendingFocus({ x: clamp(rel.x, 0, 1), y: clamp(rel.y, 0, 1) })
      setOpen(true)
      resetView()
    },
    [naturalSize, onOpen, resetView]
  )

  const onClose = useCallback(() => {
    setOpen(false)
  }, [])

  const onPreviewKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault()
        onOpen()
      }
    },
    [onOpen]
  )

  useEffect(() => {
    if (!open) return
    viewportRef.current?.focus()
  }, [open])

  useEffect(() => {
    if (!open) return

    const id = window.requestAnimationFrame(() => {
      const img = imageRef.current
      if (!img) return
      if (!img.complete) return
      if (!img.naturalWidth || !img.naturalHeight) return
      setNaturalSize({ width: img.naturalWidth, height: img.naturalHeight })
    })

    return () => window.cancelAnimationFrame(id)
  }, [open, src])

  const onViewportKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault()
        onClose()
        return
      }

      if (e.key === '+' || e.key === '=') {
        e.preventDefault()
        zoomBy(0.25)
      }

      if (e.key === '-') {
        e.preventDefault()
        zoomBy(-0.25)
      }

      if (e.key.toLowerCase() === '0') {
        e.preventDefault()
        resetView()
      }
    },
    [onClose, resetView, zoomBy]
  )

  const recomputeBaseScale = useCallback(() => {
    const safeBaseScale = computeBaseScaleValue()
    if (!safeBaseScale) return
    setBaseScale(safeBaseScale)
    setView(prev => ({
      ...prev,
      translate: clampTranslate(prev.translate, prev.zoomScale, safeBaseScale),
    }))
  }, [clampTranslate, computeBaseScaleValue])

  useEffect(() => {
    if (!open) return
    if (!pendingFocus) return

    const id = window.requestAnimationFrame(() => {
      const nextBaseScale = computeBaseScaleValue() ?? baseScale
      setBaseScale(nextBaseScale)

      const nextZoomScale = computeInitialZoomScale(nextBaseScale)
      setViewFocusedAt(pendingFocus, nextZoomScale, nextBaseScale)
      setPendingFocus(null)
    })

    return () => window.cancelAnimationFrame(id)
  }, [baseScale, computeBaseScaleValue, computeInitialZoomScale, open, pendingFocus, setViewFocusedAt])

  useEffect(() => {
    if (!open) return

    const id = window.requestAnimationFrame(() => {
      recomputeBaseScale()
    })

    const onResize = () => {
      recomputeBaseScale()
    }

    window.addEventListener('resize', onResize)
    return () => {
      window.cancelAnimationFrame(id)
      window.removeEventListener('resize', onResize)
    }
  }, [open, recomputeBaseScale])

  const transform = useMemo(() => {
    return `translate(${translate.x}px, ${translate.y}px) scale(${effectiveScale})`
  }, [effectiveScale, translate.x, translate.y])

  const onWheel = useCallback(
    (e: WheelEvent) => {
      if (!open) return
      e.preventDefault()
      const delta = e.deltaY > 0 ? -0.25 : 0.25
      zoomBy(delta)
    },
    [open, zoomBy]
  )

  const onPointerDown = useCallback(
    (e: PointerEvent) => {
      if (!canPan) return

      const target = e.target as HTMLElement | null
      if (target?.closest('[data-image-inspector-ui],button,a,input,select,textarea')) return
      ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
      dragState.current = {
        startPointer: { x: e.clientX, y: e.clientY },
        startTranslate: translate,
      }
    },
    [canPan, translate]
  )

  const onPointerMove = useCallback(
    (e: PointerEvent) => {
      if (!dragState.current) return

      const dx = e.clientX - dragState.current.startPointer.x
      const dy = e.clientY - dragState.current.startPointer.y

      const next = {
        x: dragState.current.startTranslate.x + dx,
        y: dragState.current.startTranslate.y + dy,
      }

      setView(prev => ({
        ...prev,
        translate: clampTranslate(next, prev.zoomScale, baseScale),
      }))
    },
    [baseScale, clampTranslate]
  )

  const onPointerUp = useCallback(() => {
    dragState.current = null
  }, [])

  const onPreviewImgLoad = useCallback((img: HTMLImageElement) => {
    setNaturalSize({ width: img.naturalWidth || img.width, height: img.naturalHeight || img.height })
  }, [])

  const onZoomImgLoad = useCallback(
    (img: HTMLImageElement) => {
      setNaturalSize({
        width: img.naturalWidth || img.width,
        height: img.naturalHeight || img.height,
      })
      window.requestAnimationFrame(() => {
        recomputeBaseScale()
      })
    },
    [recomputeBaseScale]
  )

  return {
    open,
    canPan,
    zoomScale,
    transform,
    previewRef,
    viewportRef,
    imageRef,
    onOpen,
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
  }
}
