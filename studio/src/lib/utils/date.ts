export type DateInput = string | number | Date | null | undefined

export type DateFormat = 'dateShort' | 'dateLong' | 'dateTimeShort' | 'dateTimeLong'

type FormatterKey = `${string}__${DateFormat}`

const formatterCache = new Map<FormatterKey, Intl.DateTimeFormat>()

function toDate(value: DateInput): Date | null {
  if (value == null) return null
  const date = value instanceof Date ? value : new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

export function toIntlLocale(language: string): string {
  if (!language) return 'de-DE'

  const normalized = language.split('-')[0]?.toLowerCase()
  if (normalized === 'de') return 'de-DE'
  if (normalized === 'en') return 'en-US'

  return language
}

function getDateTimeFormatOptions(format: DateFormat): Intl.DateTimeFormatOptions {
  switch (format) {
    case 'dateShort':
      return { year: 'numeric', month: '2-digit', day: '2-digit' }
    case 'dateLong':
      return { year: 'numeric', month: 'long', day: '2-digit' }
    case 'dateTimeShort':
      return { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }
    case 'dateTimeLong':
      return { year: 'numeric', month: 'long', day: '2-digit', hour: '2-digit', minute: '2-digit' }
    default: {
      const _exhaustiveCheck: never = format
      return _exhaustiveCheck
    }
  }
}

function getFormatter(locale: string, format: DateFormat): Intl.DateTimeFormat {
  const key: FormatterKey = `${locale}__${format}`
  const existing = formatterCache.get(key)
  if (existing) return existing

  const formatter = new Intl.DateTimeFormat(locale, getDateTimeFormatOptions(format))
  formatterCache.set(key, formatter)
  return formatter
}

export function formatDateLocale(value: DateInput, language: string, format: DateFormat, fallback = '-'): string {
  const date = toDate(value)
  if (!date) return value == null ? fallback : String(value)

  const locale = toIntlLocale(language)
  return getFormatter(locale, format).format(date)
}

export function formatDateShort(value: DateInput, language: string, fallback?: string): string {
  return formatDateLocale(value, language, 'dateShort', fallback)
}

export function formatDateLong(value: DateInput, language: string, fallback?: string): string {
  return formatDateLocale(value, language, 'dateLong', fallback)
}

export function formatDateTimeShort(value: DateInput, language: string, fallback?: string): string {
  return formatDateLocale(value, language, 'dateTimeShort', fallback)
}

export function formatDateTimeLong(value: DateInput, language: string, fallback?: string): string {
  return formatDateLocale(value, language, 'dateTimeLong', fallback)
}

type IsoDateString = string

const ISO_DATE_REGEX = /^\d{4}-\d{2}-\d{2}$/

function pad2(value: number): string {
  return String(value).padStart(2, '0')
}

function isValidUtcDateParts(year: number, month: number, day: number): boolean {
  if (!Number.isInteger(year) || !Number.isInteger(month) || !Number.isInteger(day)) return false
  if (year < 1000 || year > 9999) return false
  if (month < 1 || month > 12) return false
  if (day < 1 || day > 31) return false

  const date = new Date(Date.UTC(year, month - 1, day))
  return (
    date.getUTCFullYear() === year &&
    date.getUTCMonth() === month - 1 &&
    date.getUTCDate() === day &&
    Number.isFinite(date.getTime())
  )
}

export function isIsoDateString(value: string): boolean {
  return ISO_DATE_REGEX.test(value)
}

export function parseIsoDateString(value: string): Date | null {
  const match = ISO_DATE_REGEX.exec(value)
  if (!match) return null

  const [year, month, day] = value.split('-').map(n => Number(n))
  if (!isValidUtcDateParts(year, month, day)) return null
  return new Date(Date.UTC(year, month - 1, day))
}

export function toIsoDateString(date: Date): IsoDateString {
  // Use UTC to avoid DST edge cases when stringifying.
  return new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate())).toISOString().slice(0, 10)
}

export function formatIsoDateShort(value: IsoDateString | null | undefined, language: string, fallback = '-'): string {
  if (!value) return fallback
  const date = parseIsoDateString(value)
  if (!date) return value

  const locale = toIntlLocale(language)
  return new Intl.DateTimeFormat(locale, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    timeZone: 'UTC',
  }).format(date)
}

export function getLocaleDateInputPlaceholder(language: string): string {
  const normalized = language.split('-')[0]?.toLowerCase()
  if (normalized === 'en') return 'MM/DD/YYYY'
  return 'DD.MM.YYYY'
}

export function formatLocaleDateInput(value: IsoDateString | null | undefined, language: string): string {
  if (!value) return ''
  const date = parseIsoDateString(value)
  if (!date) return value

  const year = date.getUTCFullYear()
  const month = date.getUTCMonth() + 1
  const day = date.getUTCDate()

  const normalized = language.split('-')[0]?.toLowerCase()
  if (normalized === 'en') return `${pad2(month)}/${pad2(day)}/${year}`
  return `${pad2(day)}.${pad2(month)}.${year}`
}

export function parseLocaleDateInput(value: string, language: string): IsoDateString | null {
  const trimmed = value.trim()
  if (!trimmed) return null
  if (isIsoDateString(trimmed)) return trimmed

  const normalized = language.split('-')[0]?.toLowerCase()
  const match = /^(\d{1,2})[./-](\d{1,2})[./-](\d{4})$/.exec(trimmed)
  if (!match) return null

  const a = Number(match[1])
  const b = Number(match[2])
  const year = Number(match[3])

  const month = normalized === 'en' ? a : b
  const day = normalized === 'en' ? b : a

  if (!isValidUtcDateParts(year, month, day)) return null
  return `${year}-${pad2(month)}-${pad2(day)}`
}
