import { useMemo, useState } from 'react'
import type { TFunction } from 'i18next'

import { ActionIconButton } from '../ui/ActionIconButton'
import { DetailsIcon } from '../ui/ActionIcons'

import { isPlainObject } from './orderTraceDebug'
import { asMarker, formatMarkerSummary, type FieldMarker } from './orderFieldMappingDebug'

type Props = {
  mapping: unknown
  finalData: unknown
  t: TFunction
}

const MAX_ARRAY_ITEMS = 20
const MAX_VALUE_LEN = 160

function formatKey(key: string): string {
  return key
}

function Pill(props: { text: string }) {
  return (
    <span className="px-2 py-[2px] rounded-full border border-[color:var(--bg-card-border)] bg-[color:var(--bg)] text-[10px] font-mono">
      {props.text}
    </span>
  )
}

function MarkerRow(props: { marker: FieldMarker }) {
  const { marker } = props

  const parts = useMemo(() => formatMarkerSummary(marker), [marker])

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Pill text={`source: ${marker.source}`} />
      {parts.field ? (
        <span className="text-xs font-mono text-[color:var(--text-secondary)]">field: {parts.field}</span>
      ) : null}
      {parts.coercion ? (
        <span className="text-xs font-mono text-[color:var(--text-secondary)]">coercion: {parts.coercion}</span>
      ) : null}
      {parts.count ? (
        <span className="text-xs font-mono text-[color:var(--text-secondary)]">count: {parts.count}</span>
      ) : null}
      {parts.note ? (
        <span className="text-xs font-mono text-[color:var(--text-secondary)]">note: {parts.note}</span>
      ) : null}
    </div>
  )
}

function formatLeafValue(value: unknown): string {
  let raw: string
  if (typeof value === 'string') raw = value
  else {
    try {
      raw = JSON.stringify(value)
    } catch {
      raw = String(value)
    }
  }

  if (raw.length <= MAX_VALUE_LEN) return raw
  return `${raw.slice(0, MAX_VALUE_LEN)}…`
}

function getChild(container: unknown, key: string): unknown {
  if (Array.isArray(container)) {
    if (!/^[0-9]+$/.test(key)) return undefined
    const idx = Number(key)
    return container[idx]
  }

  if (isPlainObject(container)) {
    return (container as Record<string, unknown>)[key]
  }

  return undefined
}

function isLeafValue(value: unknown): boolean {
  if (value === null) return true
  const t = typeof value
  return t === 'string' || t === 'number' || t === 'boolean'
}

function LeafRow(props: { label: string; value: unknown; marker: FieldMarker | null; depth: number }) {
  const { label, value, marker, depth } = props

  return (
    <div className="flex items-start gap-3" style={{ paddingLeft: depth * 12 }}>
      <div className="w-56 shrink-0">
        <div className="text-xs font-mono whitespace-pre-wrap break-all">{formatKey(label)}</div>
      </div>
      <div className="w-64 shrink-0">
        <div className="text-xs font-mono whitespace-pre-wrap break-words text-[color:var(--text-secondary)]">
          {formatLeafValue(value)}
        </div>
      </div>
      <div className="min-w-0 flex-1">
        {marker ? (
          <MarkerRow marker={marker} />
        ) : (
          <span className="text-xs font-mono text-[color:var(--text-secondary)]">—</span>
        )}
      </div>
    </div>
  )
}

function Node(props: { label: string; finalValue: unknown; mappingValue: unknown; depth: number }) {
  const { label, finalValue, mappingValue, depth } = props

  // Leaves are defined by the final JSON (target structure).
  if (isLeafValue(finalValue)) {
    return <LeafRow label={label} value={finalValue} marker={asMarker(mappingValue)} depth={depth} />
  }

  if (Array.isArray(finalValue)) {
    const shown = finalValue.slice(0, MAX_ARRAY_ITEMS)
    return (
      <div style={{ paddingLeft: depth * 12 }}>
        <details className="rounded-md border border-[color:var(--bg-card-border)]" open={depth < 1}>
          <summary className="cursor-pointer select-none px-2 py-1 text-xs font-mono">
            {formatKey(label)} [{finalValue.length}]
          </summary>
          <div className="px-2 pb-2 space-y-2">
            {shown.map((item, idx) => (
              <Node
                key={idx}
                label={String(idx)}
                finalValue={item}
                mappingValue={getChild(mappingValue, String(idx))}
                depth={depth + 1}
              />
            ))}
            {finalValue.length > MAX_ARRAY_ITEMS ? (
              <div className="text-xs text-[color:var(--text-secondary)]" style={{ paddingLeft: (depth + 1) * 12 }}>
                Showing first {MAX_ARRAY_ITEMS} of {finalValue.length} items.
              </div>
            ) : null}
          </div>
        </details>
      </div>
    )
  }

  if (isPlainObject(finalValue)) {
    const entries = Object.entries(finalValue)
    return (
      <div style={{ paddingLeft: depth * 12 }}>
        <details className="rounded-md border border-[color:var(--bg-card-border)]" open={depth < 1}>
          <summary className="cursor-pointer select-none px-2 py-1 text-xs font-mono">{formatKey(label)}</summary>
          <div className="px-2 pb-2 space-y-2">
            {entries.length ? (
              entries.map(([k, v]) => (
                <Node key={k} label={k} finalValue={v} mappingValue={getChild(mappingValue, k)} depth={depth + 1} />
              ))
            ) : (
              <div className="text-xs text-[color:var(--text-secondary)]">(empty)</div>
            )}
          </div>
        </details>
      </div>
    )
  }

  // Unknown complex type in final JSON.
  return <LeafRow label={label} value={finalValue} marker={asMarker(mappingValue)} depth={depth} />
}

export function FieldMappingView(props: Props) {
  const { mapping, finalData, t } = props
  const [showRaw, setShowRaw] = useState(false)

  if (!finalData) {
    return <div className="text-sm text-[color:var(--text-secondary)]">No final JSON available.</div>
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-end gap-2">
        <ActionIconButton
          label={showRaw ? t('common.action.hideDetails') : t('common.action.showDetails')}
          onClick={() => setShowRaw(v => !v)}
        >
          <DetailsIcon />
        </ActionIconButton>
      </div>

      {showRaw ? (
        <pre className="text-xs whitespace-pre-wrap break-all">
          {JSON.stringify({ final: finalData, mapping }, null, 2)}
        </pre>
      ) : (
        <div className="space-y-2">
          {isPlainObject(finalData) ? (
            Object.entries(finalData).map(([k, v]) => (
              <Node key={k} label={k} finalValue={v} mappingValue={getChild(mapping, k)} depth={0} />
            ))
          ) : (
            <Node label="structured_data" finalValue={finalData} mappingValue={mapping} depth={0} />
          )}
        </div>
      )}
    </div>
  )
}
