import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useAppTranslation, I18N_SCOPES } from '../lib/i18n'
import { getApiBaseUrl } from '../lib/runtimeEnv'
import { joinUrl } from '../services/infrastructure/http/httpClient'

type Status = 'up' | 'degraded' | 'busy' | 'down'

type HealthState = {
  endpoint: string
  updatedAt: number
  overallStatus: Status
  xscannerStatus: Status
  aiModelStatus: Status
  details: string
}

const POLL_MS = 30_000

function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
}

function toStatus(value: unknown, fallback: Status = 'degraded'): Status {
  if (typeof value !== 'string') return fallback
  const normalized = value.trim().toLowerCase()
  if (normalized === 'healthy' || normalized === 'up' || normalized === 'ok') return 'up'
  if (normalized === 'degraded') return 'degraded'
  if (normalized === 'busy' || normalized === 'starting' || normalized === 'loading' || normalized === 'pending') {
    return 'busy'
  }
  if (normalized === 'down' || normalized === 'unhealthy') return 'down'
  return fallback
}

function labelForStatus(status: Status, t: (key: string) => string): string {
  if (status === 'up') return t('common.systemStatus.labels.up')
  if (status === 'degraded') return t('common.systemStatus.labels.degraded')
  if (status === 'busy') return t('common.systemStatus.labels.busy')
  if (status === 'down') return t('common.systemStatus.labels.down')
  return t('common.systemStatus.labels.degraded')
}

function statusUi(status: Status): { dot: string; pill: string } {
  switch (status) {
    case 'up':
      return {
        dot: 'bg-emerald-500',
        pill: 'border-emerald-300 bg-emerald-100 text-emerald-800 dark:border-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
      }
    case 'degraded':
      return {
        dot: 'bg-amber-500',
        pill: 'border-amber-300 bg-amber-100 text-amber-800 dark:border-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
      }
    case 'busy':
      return {
        dot: 'bg-sky-500',
        pill: 'border-sky-300 bg-sky-100 text-sky-800 dark:border-sky-700 dark:bg-sky-900/40 dark:text-sky-300',
      }
    case 'down':
      return {
        dot: 'bg-red-500',
        pill: 'border-red-300 bg-red-100 text-red-800 dark:border-red-700 dark:bg-red-900/40 dark:text-red-300',
      }
    default:
      return {
        dot: 'bg-slate-400',
        pill: 'border-slate-300 bg-slate-100 text-slate-700 dark:border-slate-700 dark:bg-slate-900/40 dark:text-slate-300',
      }
  }
}

function createHealthEndpoint(): string {
  const apiBase = getApiBaseUrl()
  return joinUrl(apiBase, '/health')
}

function createInitialState(): HealthState {
  return {
    endpoint: createHealthEndpoint(),
    updatedAt: Date.now(),
    overallStatus: 'busy',
    xscannerStatus: 'busy',
    aiModelStatus: 'busy',
    details: '',
  }
}

function statusFromComponentEntry(entry: unknown, fallback: Status = 'degraded'): Status {
  if (isObjectRecord(entry)) {
    return toStatus(entry.status, fallback)
  }

  return toStatus(entry, fallback)
}

function statusFromComponent(
  components: Record<string, unknown> | null,
  keys: string[],
  fallback: Status = 'degraded'
): Status {
  if (!components) return fallback

  for (const key of keys) {
    if (!(key in components)) continue
    return statusFromComponentEntry(components[key], fallback)
  }

  return fallback
}

function fallbackStatusFromHttpStatus(status: number): Status {
  if (status === 429) return 'busy'
  if (status === 503) return 'degraded'
  if (status >= 500) return 'degraded'
  if (status === 404) return 'down'
  if (status >= 400) return 'down'
  return 'degraded'
}

async function requestHealth(endpoint: string): Promise<Omit<HealthState, 'updatedAt'>> {
  const response = await fetch(endpoint)
  const text = await response.text()
  let payload: unknown = null

  if (text) {
    const contentType = response.headers.get('content-type') ?? ''
    if (contentType.includes('application/json')) {
      try {
        payload = JSON.parse(text) as unknown
      } catch {
        payload = text
      }
    } else {
      payload = text
    }
  }

  const obj = isObjectRecord(payload) ? payload : {}
  const components = isObjectRecord(obj.components) ? obj.components : null

  const overallStatus = toStatus(obj.health_status ?? obj.status, fallbackStatusFromHttpStatus(response.status))
  const xscannerStatus = statusFromComponent(components, ['xscanner'], 'degraded')
  const aiModelStatus = statusFromComponent(components, ['lora', 'ai_subsystem', 'ai', 'model', 'ai_model'], 'degraded')

  if (!response.ok) {
    const details = typeof payload === 'string' ? payload : text || `HTTP ${response.status}`

    return {
      endpoint,
      overallStatus,
      xscannerStatus,
      aiModelStatus,
      details,
    }
  }

  return {
    endpoint,
    overallStatus,
    xscannerStatus,
    aiModelStatus,
    details: typeof obj.details === 'string' ? obj.details : '',
  }
}

function SummaryRow({ title, status, t }: Readonly<{ title: string; status: Status; t: (key: string) => string }>) {
  const ui = statusUi(status)
  return (
    <div className="flex items-center justify-between rounded-xl border border-[color:var(--bg-card-border)] bg-white/35 px-3 py-2 dark:bg-white/5">
      <div className="text-sm text-[color:var(--text-primary)]">{title}</div>
      <span className={`rounded-full border px-2 py-0.5 text-xs font-medium ${ui.pill}`}>
        {labelForStatus(status, t)}
      </span>
    </div>
  )
}

export default function SystemStatusBadge() {
  const { t } = useAppTranslation(I18N_SCOPES.common)
  const rootRef = useRef<HTMLDivElement | null>(null)
  const [expanded, setExpanded] = useState(false)
  const [busy, setBusy] = useState(false)
  const [state, setState] = useState<HealthState>(createInitialState)

  const refresh = useCallback(async () => {
    setBusy(true)
    const endpoint = createHealthEndpoint()

    try {
      const next = await requestHealth(endpoint)
      setState({ ...next, updatedAt: Date.now() })
    } catch (error) {
      setState({
        endpoint,
        updatedAt: Date.now(),
        overallStatus: 'down',
        xscannerStatus: 'down',
        aiModelStatus: 'down',
        details: error instanceof Error ? error.message : String(error),
      })
    } finally {
      setBusy(false)
    }
  }, [])

  useEffect(() => {
    void refresh()
    const timer = globalThis.setInterval(() => {
      void refresh()
    }, POLL_MS)
    return () => globalThis.clearInterval(timer)
  }, [refresh])

  useEffect(() => {
    if (!expanded) return

    const onPointerDown = (event: PointerEvent) => {
      if (!rootRef.current) return
      if (rootRef.current.contains(event.target as Node)) return
      setExpanded(false)
    }

    const onEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setExpanded(false)
    }

    globalThis.addEventListener('pointerdown', onPointerDown)
    globalThis.addEventListener('keydown', onEscape)

    return () => {
      globalThis.removeEventListener('pointerdown', onPointerDown)
      globalThis.removeEventListener('keydown', onEscape)
    }
  }, [expanded])

  const displayStatus: Status = busy ? 'busy' : state.overallStatus
  const statusLabel = useMemo(() => labelForStatus(displayStatus, t), [displayStatus, t])
  const ui = statusUi(displayStatus)

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        aria-label={t('common.systemStatus.badgeLabel', { status: statusLabel })}
        title={t('common.systemStatus.badgeLabel', { status: statusLabel })}
        onClick={() => {
          void refresh()
          setExpanded(prev => !prev)
        }}
        className="inline-flex h-8 w-8 items-center justify-center rounded-full border-0 bg-transparent"
      >
        <span className={`h-2.5 w-2.5 rounded-full ${ui.dot} ${busy ? 'animate-pulse' : ''}`} />
      </button>

      {expanded ? (
        <div className="absolute right-0 z-50 mt-2 w-[22rem] rounded-2xl border border-[color:var(--bg-card-border)] bg-[color:var(--bg-secondary)] p-3 shadow-lg">
          <div className="mb-2 flex items-center justify-between gap-2">
            <div className="min-w-0 text-sm font-semibold text-[color:var(--text-primary)]">
              {t('common.systemStatus.title')}
            </div>
            <span className={`rounded-full border px-2 py-0.5 text-xs font-medium ${ui.pill}`}>{statusLabel}</span>
          </div>

          <div className="mb-3 space-y-2">
            <SummaryRow title="xscanner" status={state.xscannerStatus} t={t} />
            <SummaryRow title={t('common.systemStatus.rows.aiModel')} status={state.aiModelStatus} t={t} />
          </div>

          <div className="mt-3 border-t border-[color:var(--bg-card-border)] pt-2 text-xs text-[color:var(--text-secondary)]">
            <div>
              {t('common.systemStatus.endpoint')}: {state.endpoint}
            </div>
            <div>
              {t('common.systemStatus.lastUpdated')}: {new Date(state.updatedAt).toLocaleTimeString()}
            </div>
            {state.details ? <div className="mt-1 truncate">{state.details}</div> : null}
          </div>
        </div>
      ) : null}
    </div>
  )
}
