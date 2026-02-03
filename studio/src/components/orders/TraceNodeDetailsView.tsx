import { useMemo } from 'react'

import { RequestPayloadView } from './RequestPayloadView'
import {
  getTraceArtifacts,
  getTraceChildren,
  isPlainObject,
  prettyJson,
  TRACE_INLINE_ATTR_KEYS,
  type TraceArtifact,
  type TraceNode,
} from './orderTraceDebug'

type Props = {
  node: TraceNode
  resolveArtifactRef?: (ref: string) => { value: string; contentType?: string } | null
}

function asString(value: unknown): string | null {
  return typeof value === 'string' ? value : null
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return isPlainObject(value) ? value : null
}

function tryParseJsonRecord(value: unknown): Record<string, unknown> | null {
  if (isPlainObject(value)) return value
  if (typeof value !== 'string') return null
  try {
    const parsed: unknown = JSON.parse(value)
    return isPlainObject(parsed) ? (parsed as Record<string, unknown>) : null
  } catch {
    return null
  }
}

function asTraceNodeName(node: TraceNode): string | null {
  const name = node.name
  return typeof name === 'string' ? name : null
}

function findLlmAssistantText(payload: Record<string, unknown>): string | null {
  // OpenAI Responses API style.
  const outputText = payload.output_text
  if (typeof outputText === 'string' && outputText) return outputText

  // Chat Completions style.
  const choicesAny = payload.choices
  if (Array.isArray(choicesAny) && choicesAny.length) {
    const first = choicesAny[0]
    if (isPlainObject(first)) {
      const msg = (first as Record<string, unknown>).message
      if (isPlainObject(msg)) {
        const content = (msg as Record<string, unknown>).content
        if (typeof content === 'string' && content) return content
      }
    }
  }

  // Another Responses API representation.
  const outputAny = payload.output
  if (Array.isArray(outputAny) && outputAny.length) {
    const first = outputAny[0]
    if (isPlainObject(first)) {
      const contentAny = (first as Record<string, unknown>).content
      if (Array.isArray(contentAny) && contentAny.length) {
        const texts: string[] = []
        for (const part of contentAny) {
          if (!isPlainObject(part)) continue
          const text = (part as Record<string, unknown>).text
          if (typeof text === 'string' && text) texts.push(text)
        }
        if (texts.length) return texts.join('\n')
      }
    }
  }

  return null
}

function unescapeCommonSequences(value: string): string {
  // Best-effort for truncated JSON strings where we can't parse; improves readability for \n-heavy payloads.
  return value.replaceAll('\\n', '\n').replaceAll('\\t', '\t').replaceAll('\\r', '\r')
}

function artifactLabel(a: TraceArtifact): string {
  const key = asString(a.key) || 'artifact'
  const ct = asString(a.content_type)
  const truncated = typeof a.truncated === 'boolean' ? a.truncated : false
  const size = typeof a.size === 'number' && a.size > 0 ? ` size=${a.size}` : ''
  return `${key}${ct ? ` (${ct})` : ''}${size}${truncated ? ' truncated' : ''}`
}

export function TraceNodeDetailsView(props: Props) {
  const { node, resolveArtifactRef } = props

  const nodeName = useMemo(() => asTraceNodeName(node), [node])
  const attrs = useMemo(() => (isPlainObject(node.attrs) ? (node.attrs as Record<string, unknown>) : null), [node])
  const artifacts = useMemo(() => getTraceArtifacts(node), [node])
  const errorAny = isPlainObject(node.error) ? (node.error as Record<string, unknown>) : null

  const childNodes = useMemo(() => getTraceChildren(node), [node])
  const attemptNodes = useMemo(() => {
    if (nodeName !== 'cloud.ai_extract') return []
    return childNodes.filter(n => {
      const t = typeof n.type === 'string' ? n.type : null
      const nm = typeof n.name === 'string' ? n.name : null
      return t === 'span' && nm === 'cloud.ai_extract.attempt'
    })
  }, [childNodes, nodeName])

  const requestUrl = useMemo(() => {
    if (!attrs) return null
    const ru = attrs.request_url
    return typeof ru === 'string' ? ru : null
  }, [attrs])

  const attrsForDetails = useMemo(() => {
    if (!attrs) return null
    const out: Record<string, unknown> = {}
    const inlineKeys = new Set<string>(TRACE_INLINE_ATTR_KEYS as unknown as string[])

    for (const [k, v] of Object.entries(attrs)) {
      if (k === 'request_url') continue
      if (inlineKeys.has(k)) continue
      out[k] = v
    }

    return Object.keys(out).length ? out : null
  }, [attrs])

  if (!attrs && !artifacts.length && !errorAny) {
    return <div className="text-xs text-[color:var(--text-secondary)]">No details.</div>
  }

  return (
    <div className="space-y-3">
      {errorAny ? (
        <div className="rounded-md border border-red-400/40 bg-red-500/10 p-2 text-xs">
          <div className="font-semibold">Error</div>
          <pre className="whitespace-pre-wrap break-all">{prettyJson(errorAny)}</pre>
        </div>
      ) : null}

      {attrsForDetails ? (
        <div className="rounded-md border border-[color:var(--bg-card-border)] p-2">
          <div className="text-xs font-semibold">attrs</div>
          <pre className="mt-1 text-xs whitespace-pre-wrap break-all">{prettyJson(attrsForDetails)}</pre>
        </div>
      ) : null}

      {attemptNodes.length ? (
        <details className="rounded-md border border-[color:var(--bg-card-border)]" open>
          <summary className="cursor-pointer select-none px-2 py-1 text-xs font-semibold">
            llm.requests (attempts)
          </summary>
          <div className="px-2 pb-2 space-y-2">
            {attemptNodes.map((attemptNode, attemptIdx) => {
              const attemptAttrs = isPlainObject(attemptNode.attrs)
                ? (attemptNode.attrs as Record<string, unknown>)
                : null
              const attemptNumber =
                attemptAttrs && typeof attemptAttrs.attempt === 'number'
                  ? (attemptAttrs.attempt as number)
                  : attemptIdx + 1

              const attemptArtifacts = getTraceArtifacts(attemptNode)
              const reqArtifact = attemptArtifacts.find(a => (typeof a.key === 'string' ? a.key : '') === 'llm.request')
              const payload = reqArtifact ? tryParseJsonRecord(reqArtifact.value) : null

              return (
                <details key={attemptIdx} className="rounded-md border border-[color:var(--bg-card-border)]" open>
                  <summary className="cursor-pointer select-none px-2 py-1 text-xs">Attempt {attemptNumber}</summary>
                  <div className="px-2 pb-2">
                    {payload ? (
                      <RequestPayloadView requestUrl={requestUrl} payload={payload} attempts={[]} />
                    ) : (
                      <div className="text-xs text-[color:var(--text-secondary)]">No llm.request artifact.</div>
                    )}
                  </div>
                </details>
              )
            })}
          </div>
        </details>
      ) : null}

      {artifacts.length ? (
        <div className="space-y-2">
          <div className="text-xs font-semibold">artifacts ({artifacts.length})</div>
          {artifacts.map((a, idx) => {
            const key = asString(a.key)
            const ct = asString(a.content_type)
            const ref = asString((a as unknown as { ref?: unknown }).ref)

            const resolved = ref && resolveArtifactRef ? resolveArtifactRef(ref) : null
            const effectiveCt = resolved?.contentType ?? ct

            const plainTextValue = typeof a.value === 'string' ? a.value : (resolved?.value ?? null)

            const valueRecord = asRecord(a.value)
            const valueRecordOrParsed = tryParseJsonRecord(a.value)

            // Special-case: LLM request payloads are much nicer with RequestPayloadView.
            const showAsRequestPayload = key === 'llm.request' && (valueRecordOrParsed ?? valueRecord)

            const showAsLlmResponse = key === 'llm.response'
            const llmResponsePayload = showAsLlmResponse ? valueRecordOrParsed : null
            const llmResponseText = llmResponsePayload ? findLlmAssistantText(llmResponsePayload) : null

            const showAsPlainText = effectiveCt === 'text/plain' && plainTextValue !== null

            return (
              <details key={`${idx}:${key ?? ''}`} className="rounded-md border border-[color:var(--bg-card-border)]">
                <summary className="cursor-pointer select-none px-2 py-1 text-xs">{artifactLabel(a)}</summary>
                <div className="px-2 pb-2">
                  {ref ? (
                    <div className="mb-2 text-xs text-[color:var(--text-secondary)]">
                      ref: <span className="font-mono">{ref}</span>
                    </div>
                  ) : null}
                  {showAsRequestPayload ? (
                    <RequestPayloadView
                      requestUrl={requestUrl}
                      payload={(valueRecordOrParsed ?? valueRecord) as Record<string, unknown>}
                      attempts={[]}
                    />
                  ) : showAsLlmResponse ? (
                    <div className="space-y-2">
                      {llmResponseText ? (
                        <details className="rounded-md border border-[color:var(--bg-card-border)]" open>
                          <summary className="cursor-pointer select-none px-2 py-1 text-xs font-semibold">
                            assistant_text
                          </summary>
                          <pre className="px-2 pb-2 text-xs whitespace-pre-wrap break-words">{llmResponseText}</pre>
                        </details>
                      ) : null}

                      <details className="rounded-md border border-[color:var(--bg-card-border)]">
                        <summary className="cursor-pointer select-none px-2 py-1 text-xs font-semibold">
                          raw_response
                        </summary>
                        <div className="px-2 pb-2">
                          {llmResponsePayload ? (
                            <pre className="text-xs whitespace-pre-wrap break-all">
                              {prettyJson(llmResponsePayload)}
                            </pre>
                          ) : typeof a.value === 'string' ? (
                            <pre className="text-xs whitespace-pre-wrap break-all">
                              {unescapeCommonSequences(a.value)}
                            </pre>
                          ) : (
                            <pre className="text-xs whitespace-pre-wrap break-all">{prettyJson(a.value)}</pre>
                          )}
                        </div>
                      </details>
                    </div>
                  ) : showAsPlainText ? (
                    <pre className="text-xs whitespace-pre-wrap break-words">{plainTextValue}</pre>
                  ) : (
                    <pre className="text-xs whitespace-pre-wrap break-all">
                      {valueRecordOrParsed && ct === 'application/json'
                        ? prettyJson(valueRecordOrParsed)
                        : prettyJson(a.value ?? resolved?.value ?? null)}
                    </pre>
                  )}
                </div>
              </details>
            )
          })}
        </div>
      ) : null}
    </div>
  )
}
