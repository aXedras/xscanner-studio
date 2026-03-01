import { useMemo, type ReactNode } from 'react'
import type { TFunction } from 'i18next'

import type { TraceSpan } from './orderTraceDebug'
import { buildOrderKpis } from './orderKpis'
import { formatCurrency } from '../../lib/utils/number'

function formatMs(ms: number | null): string {
  if (ms == null) return '—'
  if (ms > 0 && ms < 1) return '<1ms'
  if (ms >= 1000) return `${(ms / 1000).toFixed(2)}s`
  return `${Math.round(ms)}ms`
}

function formatInt(value: number | null): string {
  return value == null ? '—' : String(Math.round(value))
}

function formatUsd(value: number | null, language: string): string {
  if (value == null) return '—'

  const maxFractionDigits = value < 0.01 ? 6 : 4
  return formatCurrency(value, language, 'USD', { maximumFractionDigits: maxFractionDigits })
}

function formatTokens(tokens: {
  inputTokens: number | null
  outputTokens: number | null
  totalTokens: number | null
}): string {
  return tokens.totalTokens != null
    ? `${formatInt(tokens.inputTokens)} in · ${formatInt(tokens.outputTokens)} out · ${formatInt(tokens.totalTokens)} total`
    : '—'
}

function hasPromptStats(
  stats: {
    requests: number | null
    messagesCount: number | null
    promptChars: number | null
    truncatedMessages: number | null
  } | null
): boolean {
  if (!stats) return false
  return (
    stats.requests != null ||
    stats.messagesCount != null ||
    stats.promptChars != null ||
    stats.truncatedMessages != null
  )
}

function KpiCard(props: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-md border border-[color:var(--bg-card-border)] bg-[color:var(--bg-card)] p-3">
      <div className="text-sm font-semibold mb-2">{props.title}</div>
      {props.children}
    </div>
  )
}

function KpiRows(props: { rows: Array<{ label: string; value: ReactNode }> }) {
  return (
    <dl className="grid grid-cols-[auto,1fr] gap-x-3 gap-y-1 text-sm">
      {props.rows.map(r => (
        <div key={r.label} className="contents">
          <dt className="text-[color:var(--text-secondary)]">{r.label}</dt>
          <dd className="min-w-0">
            {typeof r.value === 'string' ? (
              <span className="font-mono text-xs whitespace-pre-wrap break-all">{r.value}</span>
            ) : (
              r.value
            )}
          </dd>
        </div>
      ))}
    </dl>
  )
}

export function OrderKpiView(props: { trace: TraceSpan; meta?: unknown; t: TFunction; language: string }) {
  const { trace, meta, t, language } = props

  const kpis = useMemo(() => buildOrderKpis(trace, meta), [meta, trace])

  const hasAnyLlmUsage = kpis.llmCalls.length > 0 || (kpis.tokens.totalTokens ?? 0) > 0

  const pdfExtractLabel = t('order.detail.kpi.pdfExtract')

  const perfRows = [
    { label: t('order.detail.kpi.endToEnd'), value: formatMs(kpis.endToEndMs) },
    { label: t('order.detail.kpi.vision'), value: formatMs(kpis.visionMs) },
    { label: pdfExtractLabel, value: formatMs(kpis.pdfExtractMs) },
    { label: t('order.detail.kpi.finalize'), value: formatMs(kpis.finalizeMs) },
    { label: t('order.detail.kpi.validate'), value: formatMs(kpis.validateMs) },
  ]

  const llmRows = [
    { label: t('order.detail.kpi.provider'), value: kpis.provider ?? '—' },
    { label: t('order.detail.kpi.model'), value: kpis.model ?? '—' },
  ]

  const llmCallsBlock = kpis.llmCalls.length ? (
    <div className="space-y-2">
      {kpis.llmCalls.map((c, idx) => {
        const op = c.operation ?? 'call'
        const attemptLabel = c.attempt != null ? `attempt ${c.attempt}` : null
        const who = `${c.provider ?? '—'}/${c.model ?? '—'}`
        const tok = formatTokens(c.tokens)
        const cost = c.costUsd != null ? formatUsd(c.costUsd, language) : '—'
        const showPromptStats = hasPromptStats(c.promptStats)

        return (
          <details
            key={`${idx}-${op}-${c.attempt ?? 'na'}`}
            className="rounded-md border border-[color:var(--bg-card-border)] bg-[color:var(--bg-card)]"
          >
            <summary className="cursor-pointer select-none px-2 py-1.5 flex items-center justify-between gap-2">
              <span className="font-mono text-xs whitespace-pre-wrap break-all min-w-0">
                #{idx + 1} {op}
                {attemptLabel ? ` (${attemptLabel})` : ''}
              </span>
              <span className="font-mono text-xs text-[color:var(--text-secondary)] shrink-0">{cost}</span>
            </summary>
            <div className="px-2 pb-1.5">
              <div className="font-mono text-xs whitespace-pre-wrap break-all text-[color:var(--text-secondary)]">
                {who}
              </div>
              <div className="font-mono text-xs whitespace-pre-wrap break-all">{tok}</div>

              {showPromptStats ? (
                <div className="mt-2 grid grid-cols-[auto,1fr] gap-x-3 gap-y-1 text-sm">
                  <div className="contents">
                    <div className="text-[color:var(--text-secondary)]">{t('order.detail.kpi.requests')}</div>
                    <div className="font-mono text-xs">
                      {c.promptStats?.requests != null ? String(c.promptStats.requests) : '—'}
                    </div>
                  </div>
                  <div className="contents">
                    <div className="text-[color:var(--text-secondary)]">{t('order.detail.kpi.attempts')}</div>
                    <div className="font-mono text-xs">{c.attempt != null ? String(c.attempt) : '—'}</div>
                  </div>
                  <div className="contents">
                    <div className="text-[color:var(--text-secondary)]">{t('order.detail.kpi.promptMessages')}</div>
                    <div className="font-mono text-xs">
                      {c.promptStats?.messagesCount != null ? String(c.promptStats.messagesCount) : '—'}
                    </div>
                  </div>
                  <div className="contents">
                    <div className="text-[color:var(--text-secondary)]">{t('order.detail.kpi.promptChars')}</div>
                    <div className="font-mono text-xs">
                      {c.promptStats?.promptChars != null ? String(c.promptStats.promptChars) : '—'}
                    </div>
                  </div>
                  <div className="contents">
                    <div className="text-[color:var(--text-secondary)]">{t('order.detail.kpi.promptTrunc')}</div>
                    <div className="font-mono text-xs">
                      {c.promptStats?.truncatedMessages != null ? String(c.promptStats.truncatedMessages) : '—'}
                    </div>
                  </div>
                </div>
              ) : null}
            </div>
          </details>
        )
      })}
    </div>
  ) : (
    <span className="font-mono text-xs">—</span>
  )

  const costRows =
    kpis.costUsd != null
      ? [
          { label: t('order.detail.kpi.tokens'), value: formatTokens(kpis.tokens) },
          { label: t('order.detail.kpi.costEstimate'), value: formatUsd(kpis.costUsd, language) },
          { label: t('order.detail.kpi.costNote'), value: t('order.detail.kpi.costFromMeta') },
        ]
      : hasAnyLlmUsage
        ? [
            { label: t('order.detail.kpi.tokens'), value: formatTokens(kpis.tokens) },
            { label: t('order.detail.kpi.costEstimate'), value: t('order.detail.kpi.costUnavailable') },
            { label: t('order.detail.kpi.costNote'), value: t('order.detail.kpi.costNoteValue') },
          ]
        : [
            { label: t('order.detail.kpi.tokens'), value: formatTokens(kpis.tokens) },
            { label: t('order.detail.kpi.costEstimate'), value: t('order.detail.kpi.costUnavailable') },
            { label: t('order.detail.kpi.costNote'), value: t('order.detail.kpi.costNoLlmCalls') },
          ]

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <KpiCard title={t('order.detail.kpi.performanceTitle')}>
          <KpiRows rows={perfRows} />
        </KpiCard>
        <KpiCard title={t('order.detail.kpi.costTitle')}>
          <KpiRows rows={costRows} />
        </KpiCard>
      </div>

      <div className="grid grid-cols-1 gap-3">
        <KpiCard title={t('order.detail.kpi.llmTitle')}>
          <div className="space-y-3">
            <KpiRows rows={llmRows} />

            <div>
              <div className="text-[color:var(--text-secondary)] text-sm mb-1">{t('order.detail.kpi.calls')}</div>
              {llmCallsBlock}
            </div>
          </div>
        </KpiCard>
      </div>
    </div>
  )
}
