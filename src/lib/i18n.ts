import i18n, { type TFunction, type TOptions } from 'i18next'
import { useMemo } from 'react'
import { initReactI18next, useTranslation } from 'react-i18next'
import { logger } from './utils/logging'

import translationDE from '../locales/de/translation.json'
import translationEN from '../locales/en/translation.json'

export const I18N_SCOPES = {
  common: 'common',
  extraction: 'extraction',
  auth: 'auth',
  order: 'order',
} as const

export type I18nScope = (typeof I18N_SCOPES)[keyof typeof I18N_SCOPES]

/**
 * Translate with fallback keys
 * Try keys in order, return first match
 */
export function tWithFallback(t: TFunction, keys: readonly string[], options?: TOptions): string {
  return t(keys as unknown as string[], options as unknown as Record<string, unknown>)
}

/**
 * Translate with multiple scopes
 * Builds keys like 'scope1.key', 'scope2.key' and returns first match
 */
export function tScoped(t: TFunction, scopes: readonly string[], key: string, options?: TOptions): string {
  const scopedKeys = scopes.map(scope => `${scope}.${key}`)
  return tWithFallback(t, scopedKeys, options)
}

/**
 * Create translation function with feature-scope override
 *
 * Example:
 * - Key: 'common.toast.save.title'
 * - Scope: 'extraction'
 * - Tries: 'extraction.toast.save.title' → 'common.toast.save.title'
 */
export function createOverridableT(t: TFunction, featureScope: I18nScope): TFunction {
  return ((key: string | string[], options?: TOptions) => {
    if (!key) {
      logger.error('i18n', 'createOverridableT received an undefined/null key', { featureScope, options })
      return ''
    }

    if (Array.isArray(key)) {
      return t(key as unknown as string[], options as unknown as Record<string, unknown>)
    }

    // Feature scope override for common.* keys
    if (featureScope !== 'common' && key.startsWith('common.')) {
      const rest = key.slice('common.'.length)
      return tWithFallback(t, [`${featureScope}.${rest}`, key], options)
    }

    return t(key, options as unknown as Record<string, unknown>)
  }) as unknown as TFunction
}

/**
 * Hook with scoped translation
 *
 * Usage:
 * const { t } = useAppTranslation(I18N_SCOPES.extraction)
 * t('common.toast.save.title') // tries 'extraction.toast.save.title' first
 */
export function useAppTranslation(scope: I18nScope) {
  const { t, ...rest } = useTranslation()
  const tOverridable = useMemo(() => createOverridableT(t, scope), [t, scope])
  return { t: tOverridable, ...rest }
}

const resources = {
  de: {
    translation: translationDE,
  },
  en: {
    translation: translationEN,
  },
}

const I18N_STORAGE_KEY = 'xscanner:studio:language'

function getInitialLanguage(): 'de' | 'en' | undefined {
  if (globalThis.window === undefined) return undefined

  const saved = globalThis.localStorage.getItem(I18N_STORAGE_KEY)
  if (!saved) return undefined

  const normalized = saved.toLowerCase()
  if (normalized.startsWith('de')) return 'de'
  if (normalized.startsWith('en')) return 'en'
  return undefined
}

i18n.use(initReactI18next).init({
  resources,
  supportedLngs: ['de', 'en'],
  lng: getInitialLanguage(),
  fallbackLng: 'de',
  // Avoid i18next debug logs in the browser console.
  debug: false,
  load: 'languageOnly',
  interpolation: {
    escapeValue: false,
  },
})

if (globalThis.window !== undefined) {
  i18n.on('languageChanged', lng => {
    globalThis.localStorage.setItem(I18N_STORAGE_KEY, lng)
  })
}

export default i18n
