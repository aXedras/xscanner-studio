import type { OrderRow } from '../../services/core/order/types'

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function stripTraceFromRawSignals(rawSignals: unknown): unknown {
  if (!isPlainObject(rawSignals)) return rawSignals

  const { trace, pdf_text, marker_text, raw_text, ...rest } = rawSignals
  void trace
  void pdf_text
  void marker_text
  void raw_text
  return rest
}

const FINAL_SECTION_ORDER = ['document', 'parties', 'order_terms', 'order_items'] as const

function orderTopLevelSections<T extends Record<string, unknown>>(value: T): Record<string, unknown> {
  const ordered: Record<string, unknown> = {}

  for (const key of FINAL_SECTION_ORDER) {
    if (Object.prototype.hasOwnProperty.call(value, key)) {
      ordered[key] = value[key]
    }
  }

  const remainderKeys = Object.keys(value)
    .filter(key => !FINAL_SECTION_ORDER.includes(key as (typeof FINAL_SECTION_ORDER)[number]))
    .sort((a, b) => a.localeCompare(b))

  for (const key of remainderKeys) {
    ordered[key] = value[key]
  }

  return ordered
}

export function buildOrderDebugStrings(order: OrderRow | null): {
  finalPretty: string
  metaPretty: string
  rawSignalsPretty: string
  markerText: string
  rawText: string
  pdfText: string
  tracePretty: string
} {
  if (!order)
    return {
      finalPretty: '',
      metaPretty: '',
      rawSignalsPretty: '',
      markerText: '',
      rawText: '',
      pdfText: '',
      tracePretty: '',
    }

  const extracted = order.extracted_data as unknown

  // Support multiple persisted shapes:
  // - legacy: extracted_data = { ...structured, raw: {...} }
  // - envelope: extracted_data = { structured_data, meta, raw }
  // - response: extracted_data = { result: { structured_data, meta, raw } }
  const envelopeCandidate: unknown = isPlainObject(extracted)
    ? isPlainObject(extracted.result)
      ? extracted.result
      : extracted
    : null

  const isEnvelope =
    isPlainObject(envelopeCandidate) &&
    'structured_data' in envelopeCandidate &&
    'meta' in envelopeCandidate &&
    'raw' in envelopeCandidate

  const structuredData: unknown = isEnvelope
    ? (envelopeCandidate as Record<string, unknown>).structured_data
    : extracted

  const meta: unknown = isEnvelope ? (envelopeCandidate as Record<string, unknown>).meta : null
  const rawSignals: unknown = isEnvelope
    ? (envelopeCandidate as Record<string, unknown>).raw
    : isPlainObject(extracted)
      ? extracted.raw
      : null

  const persistedMarkerText: string =
    isEnvelope && isPlainObject(rawSignals) && typeof rawSignals.marker_text === 'string' ? rawSignals.marker_text : ''

  const persistedRawText: string =
    isEnvelope && isPlainObject(rawSignals) && typeof rawSignals.raw_text === 'string' ? rawSignals.raw_text : ''

  const persistedPdfText: string =
    isEnvelope && isPlainObject(rawSignals) && typeof rawSignals.pdf_text === 'string' ? rawSignals.pdf_text : ''

  const persistedTrace: unknown =
    isEnvelope && isPlainObject(rawSignals) && 'trace' in rawSignals
      ? (rawSignals as Record<string, unknown>).trace
      : null

  const rawSignalsForUi = stripTraceFromRawSignals(rawSignals)

  const finalData: unknown =
    isEnvelope || !isPlainObject(extracted)
      ? (structuredData ?? {})
      : (() => {
          const { raw, ...rest } = extracted
          void raw
          return rest
        })()

  const orderedFinalData = isPlainObject(finalData) ? orderTopLevelSections(finalData) : finalData

  return {
    finalPretty: JSON.stringify(orderedFinalData ?? {}, null, 2),
    metaPretty: meta ? JSON.stringify(meta ?? {}, null, 2) : '',
    rawSignalsPretty: JSON.stringify(rawSignalsForUi ?? {}, null, 2),
    markerText: persistedMarkerText,
    rawText: persistedRawText,
    pdfText: persistedPdfText,
    tracePretty: persistedTrace ? JSON.stringify(persistedTrace ?? {}, null, 2) : '',
  }
}
