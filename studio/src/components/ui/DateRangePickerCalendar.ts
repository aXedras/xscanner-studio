export function startOfUtcMonth(date: Date): Date {
  return new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), 1))
}

export function addUtcMonths(date: Date, months: number): Date {
  return new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth() + months, 1))
}

export function getDaysInUtcMonth(date: Date): number {
  const year = date.getUTCFullYear()
  const month = date.getUTCMonth()
  return new Date(Date.UTC(year, month + 1, 0)).getUTCDate()
}

export function getUtcWeekdayMondayFirst(date: Date): number {
  // JS: 0=Sun..6=Sat -> map to 0=Mon..6=Sun
  return (date.getUTCDay() + 6) % 7
}
