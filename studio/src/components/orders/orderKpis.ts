import { isPlainObject, type TraceNode, type TraceSpan } from './orderTraceDebug'
import {
  asNumber,
  asString,
  extractLlmRequestPayloadForCall,
  extractPromptStatsFromPayload,
  extractTokenCounts,
  findSpan,
  spanDurationMs,
  type TokenCounts,
} from './orderKpisHelpers'

export type OrderKpis = {
  endToEndMs: number | null
  visionMs: number | null
  pdfExtractMs: number | null
  finalizeMs: number | null
  validateMs: number | null

  llmCalls: Array<{
    operation: string | null
    attempt: number | null
    provider: string | null
    model: string | null
    tokens: TokenCounts
    costUsd: number | null
    promptStats: {
      requests: number | null
      messagesCount: number | null
      promptChars: number | null
      truncatedMessages: number | null
    } | null
  }>

  provider: string | null
  model: string | null
  tokens: TokenCounts
  costUsd: number | null
}

function extractMetaLlmUsage(meta: unknown): {
  provider: string | null
  model: string | null
  tokens: TokenCounts
  costUsd: number | null
} {
  if (typeof meta !== 'object' || meta === null || Array.isArray(meta)) {
    return {
      provider: null,
      model: null,
      tokens: { inputTokens: null, outputTokens: null, totalTokens: null },
      costUsd: null,
    }
  }

  const llmUsageAny = (meta as Record<string, unknown>).llm_usage
  if (typeof llmUsageAny !== 'object' || llmUsageAny === null || Array.isArray(llmUsageAny)) {
    return {
      provider: null,
      model: null,
      tokens: { inputTokens: null, outputTokens: null, totalTokens: null },
      costUsd: null,
    }
  }

  const llm = llmUsageAny as Record<string, unknown>
  const provider = asString(llm.provider)
  const model = asString(llm.model)
  const tokens: TokenCounts = {
    inputTokens: asNumber(llm.input_tokens),
    outputTokens: asNumber(llm.output_tokens),
    totalTokens: asNumber(llm.total_tokens),
  }
  const costUsd = asNumber(llm.cost_usd)

  return { provider, model, tokens, costUsd }
}

function extractMetaLlmCalls(meta: unknown): Array<{
  operation: string | null
  attempt: number | null
  provider: string | null
  model: string | null
  tokens: TokenCounts
  costUsd: number | null
  promptStats: {
    requests: number | null
    messagesCount: number | null
    promptChars: number | null
    truncatedMessages: number | null
  } | null
}> | null {
  if (typeof meta !== 'object' || meta === null || Array.isArray(meta)) return null

  const llmCallsAny = (meta as Record<string, unknown>).llm_calls
  if (!Array.isArray(llmCallsAny)) return null

  const out: Array<{
    operation: string | null
    attempt: number | null
    provider: string | null
    model: string | null
    tokens: TokenCounts
    costUsd: number | null
    promptStats: {
      requests: number | null
      messagesCount: number | null
      promptChars: number | null
      truncatedMessages: number | null
    } | null
  }> = []

  for (const callAny of llmCallsAny) {
    if (!isPlainObject(callAny)) continue
    const call = callAny as Record<string, unknown>
    out.push({
      operation: asString(call.operation),
      attempt: asNumber(call.attempt),
      provider: asString(call.provider),
      model: asString(call.model),
      tokens: {
        inputTokens: asNumber(call.input_tokens),
        outputTokens: asNumber(call.output_tokens),
        totalTokens: asNumber(call.total_tokens),
      },
      costUsd: asNumber(call.cost_usd),
      promptStats: null,
    })
  }

  return out
}

function computeTotalsFromCalls(
  calls: Array<{ provider: string | null; model: string | null; tokens: TokenCounts; costUsd: number | null }>
): {
  provider: string | null
  model: string | null
  tokens: TokenCounts
  costUsd: number | null
} {
  const providers = new Set(calls.map(c => c.provider).filter((v): v is string => !!v))
  const models = new Set(calls.map(c => c.model).filter((v): v is string => !!v))

  const sumOrNull = (values: Array<number | null>): number | null => {
    const nums = values.filter((v): v is number => typeof v === 'number' && Number.isFinite(v))
    return nums.length ? nums.reduce((a, b) => a + b, 0) : null
  }

  return {
    provider: providers.size === 1 ? [...providers][0] : providers.size ? 'multiple' : null,
    model: models.size === 1 ? [...models][0] : models.size ? 'multiple' : null,
    tokens: {
      inputTokens: sumOrNull(calls.map(c => c.tokens.inputTokens)),
      outputTokens: sumOrNull(calls.map(c => c.tokens.outputTokens)),
      totalTokens: sumOrNull(calls.map(c => c.tokens.totalTokens)),
    },
    costUsd: sumOrNull(calls.map(c => c.costUsd)),
  }
}

export function buildOrderKpis(traceRoot: TraceSpan, meta?: unknown): OrderKpis {
  const endToEndMs = spanDurationMs(traceRoot)

  const visionMs = spanDurationMs(findSpan(traceRoot as unknown as TraceNode, 'input.vision_prepare'))
  const pdfExtractMs = spanDurationMs(findSpan(traceRoot as unknown as TraceNode, 'strategy.pipeline'))
  const finalizeMs = (() => {
    const node = findSpan(traceRoot as unknown as TraceNode, 'finalize.finalize_order_extraction')
    return spanDurationMs(node)
  })()
  const validateMs = (() => {
    const node = findSpan(traceRoot as unknown as TraceNode, 'validate.OrderExtractedData.model_validate')
    return spanDurationMs(node)
  })()

  const cloudSpan = findSpan(traceRoot as unknown as TraceNode, 'cloud.ai_extract')
  const cloudAttrs = cloudSpan && isPlainObject(cloudSpan.attrs) ? (cloudSpan.attrs as Record<string, unknown>) : null
  const providerFromTrace = cloudAttrs ? asString(cloudAttrs.provider) : null
  const modelFromTrace = cloudAttrs ? asString(cloudAttrs.model) : null
  const tokensFromTrace = extractTokenCounts(cloudAttrs ? cloudAttrs.usage : null)

  const llmCallsFromMeta = extractMetaLlmCalls(meta) ?? []
  const llmCalls = llmCallsFromMeta.map(call => {
    const payload = extractLlmRequestPayloadForCall(traceRoot, call.operation, call.attempt)
    const stats = extractPromptStatsFromPayload(payload)
    const anyValue = stats.messagesCount != null || stats.promptChars != null || stats.truncatedMessages != null
    return {
      ...call,
      promptStats: anyValue
        ? {
            requests: payload ? (asNumber(payload.request_attempts) ?? 1) : null,
            messagesCount: stats.messagesCount,
            promptChars: stats.promptChars,
            truncatedMessages: stats.truncatedMessages,
          }
        : null,
    }
  })

  const metaUsage = extractMetaLlmUsage(meta)

  const totals = (() => {
    if (llmCalls.length) return computeTotalsFromCalls(llmCalls)
    if (metaUsage.provider || metaUsage.model || metaUsage.costUsd || metaUsage.tokens.totalTokens != null)
      return metaUsage
    return { provider: providerFromTrace, model: modelFromTrace, tokens: tokensFromTrace, costUsd: null }
  })()

  const provider = totals.provider
  const model = totals.model
  const tokens = totals.tokens
  const costUsd = totals.costUsd

  // Prompt stats are displayed per call.

  return {
    endToEndMs,
    visionMs,
    pdfExtractMs,
    finalizeMs,
    validateMs,
    llmCalls,
    provider,
    model,
    tokens,
    costUsd,
  }
}

export function formatOrderKpisForCopy(kpis: OrderKpis): string {
  return JSON.stringify(kpis, null, 2)
}

export function buildOrderKpiCopyText(traceRoot: TraceSpan | null, meta?: unknown): string {
  if (!traceRoot) return ''
  return formatOrderKpisForCopy(buildOrderKpis(traceRoot, meta))
}
