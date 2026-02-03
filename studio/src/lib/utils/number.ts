import { toIntlLocale } from './date'

type NumberStyle = 'decimal' | 'currency' | 'percent'

type FormatterKey = string

const formatterCache = new Map<FormatterKey, Intl.NumberFormat>()

function getFormatter(locale: string, options: Intl.NumberFormatOptions): Intl.NumberFormat {
  const keyParts = [
    locale,
    String(options.style ?? 'decimal'),
    String(options.currency ?? ''),
    String(options.currencyDisplay ?? ''),
    String(options.useGrouping ?? ''),
    String(options.minimumFractionDigits ?? ''),
    String(options.maximumFractionDigits ?? ''),
    String(options.minimumSignificantDigits ?? ''),
    String(options.maximumSignificantDigits ?? ''),
  ]
  const key: FormatterKey = keyParts.join('__')

  const existing = formatterCache.get(key)
  if (existing) return existing

  const formatter = new Intl.NumberFormat(locale, options)
  formatterCache.set(key, formatter)
  return formatter
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value)
}

export function formatNumber(
  value: number | null | undefined,
  language: string,
  options?: Intl.NumberFormatOptions & { style?: NumberStyle }
): string {
  if (!isFiniteNumber(value)) return '—'

  const locale = toIntlLocale(language)
  const fmt = getFormatter(locale, {
    style: options?.style ?? 'decimal',
    ...options,
  })

  return fmt.format(value)
}

export function formatDecimal(
  value: number | null | undefined,
  language: string,
  options?: Omit<Intl.NumberFormatOptions, 'style'>
): string {
  return formatNumber(value, language, { style: 'decimal', ...options })
}

export function formatCurrency(
  value: number | null | undefined,
  language: string,
  currency: string,
  options?: Omit<Intl.NumberFormatOptions, 'style' | 'currency'>
): string {
  return formatNumber(value, language, { style: 'currency', currency, ...options })
}

/**
 * Formats a number for use in an <input> value:
 * - locale-aware decimal separator
 * - no thousands grouping (to keep parsing simple)
 */
export function formatDecimalInput(
  value: number | null | undefined,
  language: string,
  options?: Omit<Intl.NumberFormatOptions, 'style' | 'useGrouping'>
): string {
  if (!isFiniteNumber(value)) return ''
  return formatNumber(value, language, { style: 'decimal', useGrouping: false, ...options })
}
