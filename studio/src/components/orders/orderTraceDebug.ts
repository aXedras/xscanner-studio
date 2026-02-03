export type TraceArtifact = {
  key?: unknown
  content_type?: unknown
  value?: unknown
  ref?: unknown
  size?: unknown
  truncated?: unknown
}

export type TraceSpan = {
  type?: unknown
  name?: unknown
  start_ms?: unknown
  end_ms?: unknown
  duration_ms?: unknown
  status?: unknown
  summary?: unknown
  attrs?: unknown
  artifacts?: unknown
  children?: unknown
  error?: unknown
}

export type TraceEvent = {
  type?: unknown
  name?: unknown
  at_ms?: unknown
  attrs?: unknown
}

export type TraceNode = Record<string, unknown>

export const TRACE_INLINE_ATTR_KEYS = [
  'decision',
  'reason',
  'rule_id',
  'strategy',
  'strategy_impl',
  'provider',
  'model',
  'attempt',
  'issuer',
  'doc_type',
  'mode',
  'requested_strategy',
  'lines',
  'tables',
  'key_values',
  'raw_text_len',
  'text_len_before',
  'text_len_after',
  'doc_type_candidates_count',
  'has_document_number',
  'has_document_date',
  'order_items_table_detected',
] as const

const MAX_FACT_VALUE_LEN = 48

function formatFactValue(value: unknown): string | null {
  if (typeof value === 'string') {
    const trimmed = value.trim()
    if (!trimmed) return null
    if (trimmed.length <= MAX_FACT_VALUE_LEN) return trimmed
    return `${trimmed.slice(0, MAX_FACT_VALUE_LEN)}…`
  }
  if (typeof value === 'number' && Number.isFinite(value)) return String(value)
  if (typeof value === 'boolean') return value ? 'true' : 'false'
  return null
}

function pushAttrFact(parts: string[], attrs: Record<string, unknown> | null, key: string, label?: string): void {
  if (!attrs) return
  const v = formatFactValue(attrs[key])
  if (v === null) return
  const k = label ?? key
  parts.push(`${k}=${v}`)
}

export function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

export function parseTrace(tracePretty: string): TraceSpan | null {
  if (!tracePretty) return null
  try {
    const parsed: unknown = JSON.parse(tracePretty)
    if (!isPlainObject(parsed)) return null
    const type = parsed.type
    if (type !== 'span') return null
    return parsed as TraceSpan
  } catch {
    return null
  }
}

export function prettyJson(value: unknown): string {
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}

export function traceNodeTitle(node: TraceNode): string {
  const type = typeof node.type === 'string' ? node.type : ''
  const name = typeof node.name === 'string' ? node.name : ''
  return type === 'event' ? `${name}` : `${name}`
}

export function traceNodeFacts(node: TraceNode): string[] {
  const parts: string[] = []

  const type = typeof node.type === 'string' ? node.type : ''
  if (type === 'span') {
    if (typeof node.duration_ms === 'number') parts.push(`${Math.round(node.duration_ms)}ms`)
    const status = typeof node.status === 'string' ? node.status : null
    if (status) parts.push(status)

    const attrs = isPlainObject(node.attrs) ? (node.attrs as Record<string, unknown>) : null
    const strategy = attrs && typeof attrs.strategy === 'string' ? (attrs.strategy as string) : null
    const impl = attrs && typeof attrs.strategy_impl === 'string' ? (attrs.strategy_impl as string) : null
    const provider = attrs && typeof attrs.provider === 'string' ? (attrs.provider as string) : null
    const model = attrs && typeof attrs.model === 'string' ? (attrs.model as string) : null
    const attempt = attrs && typeof attrs.attempt === 'number' ? (attrs.attempt as number) : null

    if (strategy) parts.push(`strategy=${strategy}`)
    if (impl) parts.push(`impl=${impl}`)
    if (provider) parts.push(`provider=${provider}`)
    if (model) parts.push(`model=${model}`)
    if (attempt !== null) parts.push(`attempt=${attempt}`)

    const summary = typeof node.summary === 'string' ? node.summary : null
    if (summary) parts.push(summary)

    // Inline important attrs to avoid click fatigue.
    // Keep this list short and scalar-only (large blobs belong in artifacts).
    pushAttrFact(parts, attrs, 'decision')
    pushAttrFact(parts, attrs, 'reason')
    pushAttrFact(parts, attrs, 'rule_id', 'rule')
    pushAttrFact(parts, attrs, 'issuer')
    pushAttrFact(parts, attrs, 'doc_type')
    pushAttrFact(parts, attrs, 'mode')
    pushAttrFact(parts, attrs, 'requested_strategy')

    pushAttrFact(parts, attrs, 'lines')
    pushAttrFact(parts, attrs, 'tables')
    pushAttrFact(parts, attrs, 'key_values')
    pushAttrFact(parts, attrs, 'raw_text_len')

    pushAttrFact(parts, attrs, 'text_len_before')
    pushAttrFact(parts, attrs, 'text_len_after')
    pushAttrFact(parts, attrs, 'doc_type_candidates_count')
    pushAttrFact(parts, attrs, 'has_document_number')
    pushAttrFact(parts, attrs, 'has_document_date')
    pushAttrFact(parts, attrs, 'order_items_table_detected')
  }

  if (type === 'event') {
    if (typeof node.at_ms === 'number') parts.push(`@${Math.round(node.at_ms)}ms`)

    const attrs = isPlainObject(node.attrs) ? (node.attrs as Record<string, unknown>) : null
    // Only a few scalar event attrs; the point is to keep the tree readable.
    pushAttrFact(parts, attrs, 'decision')
    pushAttrFact(parts, attrs, 'reason')
    pushAttrFact(parts, attrs, 'rule_id', 'rule')
    pushAttrFact(parts, attrs, 'strategy')
    pushAttrFact(parts, attrs, 'mode')
    pushAttrFact(parts, attrs, 'requested_strategy')
  }

  return parts
}

export function getTraceChildren(node: TraceNode): TraceNode[] {
  if (!isPlainObject(node)) return []
  const children = (node as Record<string, unknown>).children
  return Array.isArray(children) ? (children.filter(isPlainObject) as TraceNode[]) : []
}

export function getTraceArtifacts(node: TraceNode): TraceArtifact[] {
  if (!isPlainObject(node)) return []
  const artifacts = (node as Record<string, unknown>).artifacts
  return Array.isArray(artifacts) ? (artifacts.filter(isPlainObject) as TraceArtifact[]) : []
}
