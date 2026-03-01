type RuntimeEnv = Partial<Record<string, string>>

declare global {
  interface Window {
    __ENV__?: RuntimeEnv
  }
}

const readRuntimeEnv = (): RuntimeEnv => {
  if (typeof window === 'undefined') return {}
  return window.__ENV__ || {}
}

export const getRuntimeEnv = (key: string): string | undefined => {
  const value = readRuntimeEnv()[key]
  const trimmed = (value || '').trim()
  return trimmed ? trimmed : undefined
}
