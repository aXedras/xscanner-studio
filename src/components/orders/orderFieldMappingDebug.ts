import { isPlainObject } from './orderTraceDebug'

function asString(value: unknown): string | null {
  return typeof value === 'string' ? value : null
}

function formatMarkerValue(value: unknown): string | null {
  if (typeof value === 'string') return value
  if (typeof value === 'number' && Number.isFinite(value)) return String(value)
  if (typeof value === 'boolean') return value ? 'true' : 'false'
  return null
}

type Marker = {
  source: string
  field?: unknown
  coercion?: unknown
  note?: unknown
  count?: unknown
}

export type FieldMarker = Marker

export function asMarker(value: unknown): FieldMarker | null {
  if (!isPlainObject(value)) return null
  const src = (value as Record<string, unknown>).source
  if (typeof src === 'string' && src.length > 0) return value as FieldMarker
  return null
}

export function formatMarkerSummary(marker: FieldMarker): {
  field: string | null
  coercion: string | null
  note: string | null
  count: string | null
} {
  return {
    field: formatMarkerValue(marker.field),
    coercion: formatMarkerValue(marker.coercion),
    note: formatMarkerValue(marker.note),
    count: formatMarkerValue(marker.count),
  }
}

function markerToDisplayString(marker: FieldMarker): string {
  const parts: string[] = []

  parts.push(`source: ${marker.source}`)

  const fieldStr = formatMarkerValue(marker.field)
  if (fieldStr) parts.push(`field: ${fieldStr}`)

  const coercionStr = formatMarkerValue(marker.coercion)
  if (coercionStr) parts.push(`coercion: ${coercionStr}`)

  const countStr = formatMarkerValue(marker.count)
  if (countStr) parts.push(`count: ${countStr}`)

  const noteStr = formatMarkerValue(marker.note)
  if (noteStr) parts.push(`note: ${noteStr}`)

  return parts.join(', ')
}

export function extractFieldMapping(metaAny: unknown): unknown {
  if (!isPlainObject(metaAny)) return null
  const fm = (metaAny as Record<string, unknown>).field_mapping
  return fm === undefined ? null : fm
}

export function formatFieldMappingForUi(value: unknown): unknown {
  const marker = asMarker(value)
  if (marker) return markerToDisplayString(marker)

  if (Array.isArray(value)) {
    return value.map(v => formatFieldMappingForUi(v))
  }

  if (isPlainObject(value)) {
    const out: Record<string, unknown> = {}
    for (const [k, v] of Object.entries(value)) {
      // Keep keys as-is; preserve target structure.
      out[asString(k) ?? String(k)] = formatFieldMappingForUi(v)
    }
    return out
  }

  // Unknown shape; return as-is for visibility.
  return value
}
