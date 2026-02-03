import { useMemo, useState } from 'react'

import { isPlainObject, prettyJson } from './orderTraceDebug'

type Props = {
  requestUrl: string | null
  payload: Record<string, unknown> | null
  attempts: Array<Record<string, unknown>>
}

type PayloadMessage = {
  role: string
  content: string
  content_len?: number
  content_truncated?: boolean
}

function asMessages(payload: Record<string, unknown>): PayloadMessage[] {
  const messagesAny = payload.messages
  if (!Array.isArray(messagesAny)) return []

  const out: PayloadMessage[] = []
  for (const m of messagesAny) {
    if (!isPlainObject(m)) continue
    const role = typeof m.role === 'string' ? m.role : ''
    const content = typeof m.content === 'string' ? m.content : String(m.content ?? '')
    const contentLen = typeof m.content_len === 'number' ? m.content_len : undefined
    const truncated = typeof m.content_truncated === 'boolean' ? m.content_truncated : undefined
    out.push({ role, content, content_len: contentLen, content_truncated: truncated })
  }

  return out
}

function pickScalar(payload: Record<string, unknown>, key: string): string | number | boolean | null {
  const v = payload[key]
  if (typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean') return v
  if (v === null) return null
  return null
}

export function RequestPayloadView(props: Props) {
  const { requestUrl, payload, attempts } = props

  const [showRetries, setShowRetries] = useState(false)
  const initialMessages = payload ? asMessages(payload) : []
  const [openMessages, setOpenMessages] = useState<Record<string, boolean>>(() => {
    const next: Record<string, boolean> = {}
    for (let i = 0; i < initialMessages.length; i += 1) {
      const m = initialMessages[i]
      next[`${i}:${m.role}`] = m.role !== 'system'
    }
    return next
  })

  const messages = useMemo(() => (payload ? asMessages(payload) : []), [payload])

  const summary = useMemo(() => {
    if (!payload) return []

    const fields: Array<{ label: string; value: string }> = []
    const keys = ['model', 'temperature', 'max_tokens', 'max_completion_tokens', 'reasoning_effort', 'response_format']

    for (const key of keys) {
      if (key === 'response_format') {
        const v = payload[key]
        if (isPlainObject(v)) fields.push({ label: key, value: prettyJson(v) })
        continue
      }

      const v = pickScalar(payload, key)
      if (v === null) continue
      fields.push({ label: key, value: String(v) })
    }

    return fields
  }, [payload])

  const otherPayload = useMemo(() => {
    if (!payload) return null
    const { messages: _messages, ...rest } = payload
    void _messages
    return rest
  }, [payload])

  if (!payload) {
    return <div className="text-sm text-[color:var(--text-secondary)]">No request payload available.</div>
  }

  return (
    <div className="space-y-3">
      {requestUrl ? (
        <div className="text-xs">
          <div className="text-[color:var(--text-secondary)]">request_url</div>
          <a className="link break-all" href={requestUrl} target="_blank" rel="noreferrer">
            {requestUrl}
          </a>
        </div>
      ) : null}

      {summary.length ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {summary.map(row => (
            <div key={row.label} className="text-xs">
              <div className="text-[color:var(--text-secondary)]">{row.label}</div>
              <div className="font-mono whitespace-pre-wrap break-all">{row.value}</div>
            </div>
          ))}
        </div>
      ) : null}

      {messages.length ? (
        <div className="space-y-2">
          <div className="text-xs font-semibold">messages ({messages.length})</div>
          {messages.map((m, idx) => (
            <div key={idx} className="rounded-md border border-[color:var(--bg-card-border)]">
              <details
                open={!!openMessages[`${idx}:${m.role}`]}
                onToggle={e => {
                  const open = (e.currentTarget as HTMLDetailsElement).open
                  const key = `${idx}:${m.role}`
                  setOpenMessages(prev => (prev[key] === open ? prev : { ...prev, [key]: open }))
                }}
              >
                <summary className="cursor-pointer select-none px-2 py-1 text-xs flex items-center justify-between gap-2">
                  <div className="font-mono">{m.role || 'unknown'}</div>
                  <div className="text-[color:var(--text-secondary)]">
                    {typeof m.content_len === 'number' ? `len=${m.content_len}` : null}
                    {m.content_truncated ? ' · truncated' : null}
                  </div>
                </summary>
                <pre className="px-2 pb-2 text-xs whitespace-pre-wrap break-words">{m.content}</pre>
              </details>
            </div>
          ))}
        </div>
      ) : null}

      {otherPayload && Object.keys(otherPayload).length ? (
        <details className="rounded-md border border-[color:var(--bg-card-border)]">
          <summary className="cursor-pointer select-none px-2 py-1 text-xs font-semibold">other_fields</summary>
          <div className="px-2 pb-2">
            <pre className="text-xs whitespace-pre-wrap break-all">{prettyJson(otherPayload)}</pre>
          </div>
        </details>
      ) : null}

      {attempts.length > 1 ? (
        <div>
          <button type="button" className="btn btn-outline btn-sm" onClick={() => setShowRetries(v => !v)}>
            {showRetries ? 'Hide retries' : `Show retries (${attempts.length - 1})`}
          </button>

          {showRetries ? (
            <div className="mt-2 space-y-2">
              {attempts.map((attempt, attemptIdx) => (
                <details key={attemptIdx} className="rounded border border-[color:var(--bg-card-border)]">
                  <summary className="cursor-pointer select-none px-2 py-1 text-xs">Attempt {attemptIdx + 1}</summary>
                  <div className="px-2 pb-2">
                    <pre className="text-xs whitespace-pre-wrap break-all">{prettyJson(attempt)}</pre>
                  </div>
                </details>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}
