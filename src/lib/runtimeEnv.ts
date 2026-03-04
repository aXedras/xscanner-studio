type RuntimeEnv = Partial<Record<string, string>>

const API_BASE_OVERRIDE_KEY = 'xscanner.studio.apiBaseUrl'
export const DEFAULT_API_BASE_URL = 'http://localhost:9000'

declare global {
  interface Window {
    __ENV__?: RuntimeEnv
  }
}

const readRuntimeEnv = (): RuntimeEnv => {
  if (globalThis.window === undefined) return {}
  return globalThis.window.__ENV__ || {}
}

function normalizeUrl(value: string | undefined): string | undefined {
  const trimmed = (value || '').trim()
  if (!trimmed) return undefined
  return trimmed.replace(/\/+$/, '')
}

function readApiBaseOverride(): string | undefined {
  if (globalThis.window === undefined) return undefined
  try {
    return normalizeUrl(globalThis.localStorage.getItem(API_BASE_OVERRIDE_KEY) || undefined)
  } catch {
    return undefined
  }
}

export const getRuntimeEnv = (key: string): string | undefined => {
  const value = readRuntimeEnv()[key]
  const trimmed = (value || '').trim()
  return trimmed || undefined
}

export const getApiBaseUrl = (): string => {
  const override = readApiBaseOverride()
  if (override) return override

  const runtime = normalizeUrl(getRuntimeEnv('VITE_API_URL'))
  if (runtime) return runtime

  const fromBuild = normalizeUrl(import.meta.env.VITE_API_URL as string | undefined)
  if (fromBuild) return fromBuild

  return DEFAULT_API_BASE_URL
}

export const setApiBaseUrlOverride = (url: string): void => {
  if (globalThis.window === undefined) return
  const normalized = normalizeUrl(url)
  if (!normalized) {
    globalThis.localStorage.removeItem(API_BASE_OVERRIDE_KEY)
    return
  }
  globalThis.localStorage.setItem(API_BASE_OVERRIDE_KEY, normalized)
}
