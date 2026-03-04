import { useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { useAppTranslation, I18N_SCOPES } from '../lib/i18n'
import { DEFAULT_API_BASE_URL, getApiBaseUrl, setApiBaseUrlOverride } from '../lib/runtimeEnv'
import { PageHeader } from '../components/layout/PageHeader'

const HEALTHCHECK_TIMEOUT_MS = 4_000
const HEALTH_PATHS = ['/api/v1/health', '/health'] as const

function normalizeUrlInput(value: string): string {
  return value.trim().replace(/\/+$/, '')
}

function isValidAbsoluteUrl(value: string): boolean {
  try {
    const parsed = new URL(value)
    return parsed.protocol === 'http:' || parsed.protocol === 'https:'
  } catch {
    return false
  }
}

async function checkHealthEndpointReachable(baseUrl: string): Promise<{ ok: boolean; status?: number }> {
  const controller = new AbortController()
  const timeoutId = globalThis.setTimeout(() => controller.abort(), HEALTHCHECK_TIMEOUT_MS)

  try {
    let lastStatus: number | undefined

    for (const path of HEALTH_PATHS) {
      const response = await fetch(`${baseUrl}${path}`, {
        method: 'GET',
        signal: controller.signal,
      })

      if (response.ok) {
        return { ok: true, status: response.status }
      }

      lastStatus = response.status
    }

    return { ok: false, status: lastStatus }
  } catch {
    return { ok: false }
  } finally {
    globalThis.clearTimeout(timeoutId)
  }
}

export default function SettingsPage() {
  const { t } = useAppTranslation(I18N_SCOPES.common)
  const [apiUrl, setApiUrl] = useState<string>(getApiBaseUrl())
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const defaultInfo = useMemo(() => t('common.settings.defaultInfo', { url: DEFAULT_API_BASE_URL }), [t])

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const normalized = normalizeUrlInput(apiUrl)

    if (!isValidAbsoluteUrl(normalized)) {
      setError(t('common.settings.invalidUrl'))
      return
    }

    setSaving(true)

    const health = await checkHealthEndpointReachable(normalized)
    if (!health.ok) {
      setSaving(false)
      setError(
        t('common.settings.unreachableUrl', {
          url: normalized,
          status: health.status ? ` (HTTP ${health.status})` : '',
        })
      )
      return
    }

    setApiBaseUrlOverride(normalized)
    globalThis.location.reload()
  }

  const onReset = () => {
    setApiBaseUrlOverride(DEFAULT_API_BASE_URL)
    globalThis.location.reload()
  }

  return (
    <section className="space-y-6">
      <PageHeader
        title={t('common.settings.title')}
        subtitle={t('common.settings.subtitle')}
        backLabel={t('common.action.back')}
      />

      <form
        onSubmit={onSubmit}
        className="rounded-2xl border border-[color:var(--bg-card-border)] bg-[color:var(--bg-card)] p-6"
      >
        <label className="block text-sm font-medium text-[color:var(--text-primary)]" htmlFor="settings-api-url">
          {t('common.settings.backendUrl')}
        </label>
        <p className="mt-1 text-xs text-[color:var(--text-secondary)]">{t('common.settings.backendHint')}</p>
        <input
          id="settings-api-url"
          className="input mt-3 w-full"
          value={apiUrl}
          onChange={event => {
            setApiUrl(event.target.value)
            if (error) setError(null)
          }}
          placeholder={DEFAULT_API_BASE_URL}
          autoComplete="off"
        />

        {error ? <p className="mt-2 text-xs text-red-600 dark:text-red-400">{error}</p> : null}

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {t('common.settings.save')}
          </button>
          <button type="button" onClick={onReset} className="btn btn-outline" disabled={saving}>
            {t('common.settings.reset')}
          </button>
          <span className="text-xs text-[color:var(--text-secondary)]">{defaultInfo}</span>
        </div>
      </form>
    </section>
  )
}
