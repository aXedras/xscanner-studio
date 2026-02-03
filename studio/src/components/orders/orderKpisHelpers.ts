import { getTraceArtifacts, getTraceChildren, isPlainObject, type TraceNode, type TraceSpan } from './orderTraceDebug'

export function asNumber(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) return value
  if (typeof value === 'string') {
    const trimmed = value.trim()
    if (!trimmed) return null
    // Only accept plain numeric strings (avoid parsing '25ms' / '1.2s').
    if (!/^-?\d+(?:\.\d+)?$/.test(trimmed)) return null
    const parsed = Number(trimmed)
    return Number.isFinite(parsed) ? parsed : null
  }
  return null
}

export function asString(value: unknown): string | null {
  return typeof value === 'string' && value.trim() ? value : null
}

export function isSpan(node: TraceNode): node is TraceSpan {
  return isPlainObject(node) && node.type === 'span'
}

export function iterNodes(root: TraceNode): TraceNode[] {
  const out: TraceNode[] = []
  const walk = (node: TraceNode) => {
    out.push(node)
    for (const child of getTraceChildren(node)) walk(child)
  }
  walk(root)
  return out
}

export function findSpan(root: TraceNode, name: string): TraceSpan | null {
  for (const node of iterNodes(root)) {
    if (!isSpan(node)) continue
    if (node.name === name) return node
  }
  return null
}

export function spanDurationMs(node: TraceSpan | null): number | null {
  if (!node) return null

  const duration = asNumber(node.duration_ms)
  if (duration != null) return duration

  const start = asNumber(node.start_ms)
  const end = asNumber(node.end_ms)
  if (start != null && end != null) return end - start

  // Fallback: some traces are persisted before the root is finished (missing duration/end).
  // In that case, approximate duration from the latest end_ms in the subtree.
  if (start != null) {
    const ends = iterNodes(node as unknown as TraceNode)
      .filter(isSpan)
      .map(sp => asNumber(sp.end_ms))
      .filter((v): v is number => v != null)

    if (ends.length) return Math.max(...ends) - start
  }

  return null
}

export type TokenCounts = {
  inputTokens: number | null
  outputTokens: number | null
  totalTokens: number | null
}

export function extractTokenCounts(usage: unknown): TokenCounts {
  // Backend uses AiUsage: { input_tokens, output_tokens, total_tokens }
  // Some providers might return { prompt_tokens, completion_tokens, total_tokens }
  if (typeof usage !== 'object' || usage === null || Array.isArray(usage)) {
    return { inputTokens: null, outputTokens: null, totalTokens: null }
  }

  const anyUsage = usage as Record<string, unknown>

  const inputTokens = asNumber(anyUsage.input_tokens) ?? asNumber(anyUsage.prompt_tokens)
  const outputTokens = asNumber(anyUsage.output_tokens) ?? asNumber(anyUsage.completion_tokens)
  const totalTokens = asNumber(anyUsage.total_tokens)

  return { inputTokens, outputTokens, totalTokens }
}

export function extractPromptStatsFromPayload(payload: unknown): {
  messagesCount: number | null
  promptChars: number | null
  truncatedMessages: number | null
} {
  if (typeof payload !== 'object' || payload === null || Array.isArray(payload)) {
    return { messagesCount: null, promptChars: null, truncatedMessages: null }
  }

  const messagesAny = (payload as Record<string, unknown>).messages
  if (!Array.isArray(messagesAny)) {
    return { messagesCount: null, promptChars: null, truncatedMessages: null }
  }

  let promptChars = 0
  let truncatedMessages = 0
  let count = 0

  for (const m of messagesAny) {
    if (typeof m !== 'object' || m === null || Array.isArray(m)) continue
    const msg = m as Record<string, unknown>
    count += 1

    // Non-vision messages: { content_len, content_truncated }
    const len = asNumber(msg.content_len)
    if (len != null) promptChars += len
    if (msg.content_truncated === true) truncatedMessages += 1

    // Vision user messages: { content: [{ type: 'text', text_len, text_truncated }, ...] }
    const contentAny = msg.content
    if (Array.isArray(contentAny)) {
      for (const partAny of contentAny) {
        if (typeof partAny !== 'object' || partAny === null || Array.isArray(partAny)) continue
        const part = partAny as Record<string, unknown>
        if (part.type !== 'text') continue
        const partLen = asNumber(part.text_len)
        if (partLen != null) promptChars += partLen
        if (part.text_truncated === true) truncatedMessages += 1
      }
    }
  }

  return {
    messagesCount: count,
    promptChars: count ? promptChars : null,
    truncatedMessages: count ? truncatedMessages : null,
  }
}

export function extractLastCloudRequestPayload(traceRoot: TraceSpan): Record<string, unknown> | null {
  return extractCloudRequestPayload(traceRoot, null)
}

export function extractCloudRequestPayload(
  traceRoot: TraceSpan,
  attempt: number | null
): Record<string, unknown> | null {
  const cloudSpan = findSpan(traceRoot as unknown as TraceNode, 'cloud.ai_extract')
  if (!cloudSpan) return null

  const attemptSpans = getTraceChildren(cloudSpan as unknown as TraceNode)
    .filter(isSpan)
    .filter(sp => sp.name === 'cloud.ai_extract.attempt')

  if (!attemptSpans.length) return null

  const idx = (() => {
    if (attempt == null) return attemptSpans.length - 1
    const i = Math.round(attempt) - 1
    if (i < 0 || i >= attemptSpans.length) return attemptSpans.length - 1
    return i
  })()

  const selectedAttempt = attemptSpans[idx]
  const artifacts = getTraceArtifacts(selectedAttempt as unknown as TraceNode)
  const payloadArtifact = artifacts.find(a => a.key === 'llm.request')
  return isPlainObject(payloadArtifact?.value) ? (payloadArtifact?.value as Record<string, unknown>) : null
}

export function extractLlmRequestPayloadForCall(
  traceRoot: TraceSpan,
  operation: string | null,
  attempt: number | null
): Record<string, unknown> | null {
  if (!operation) return null

  // Cloud calls keep request payloads under explicit per-attempt spans.
  if (operation === 'cloud.ai_extract') {
    return extractCloudRequestPayload(traceRoot, attempt)
  }

  // Generic: find the span for the operation, then scan its subtree for llm.request artifacts.
  const candidates = iterNodes(traceRoot as unknown as TraceNode)
    .filter(isSpan)
    .filter(sp => sp.name === operation)
  if (!candidates.length) return null

  const selected = (() => {
    if (attempt == null) return candidates[candidates.length - 1]
    const exact = candidates.find(sp => {
      const attrs = isPlainObject(sp.attrs) ? (sp.attrs as Record<string, unknown>) : null
      return asNumber(attrs?.attempt) === attempt
    })
    return exact ?? candidates[candidates.length - 1]
  })()

  const nodes = iterNodes(selected as unknown as TraceNode)
  for (let i = nodes.length - 1; i >= 0; i -= 1) {
    const node = nodes[i]
    if (!isSpan(node)) continue
    const artifacts = getTraceArtifacts(node as unknown as TraceNode)
    const payloadArtifact = artifacts.find(a => a.key === 'llm.request')
    if (isPlainObject(payloadArtifact?.value)) return payloadArtifact?.value as Record<string, unknown>
  }

  return null
}
