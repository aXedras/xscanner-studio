import { useMemo } from 'react'
import type { ReactNode } from 'react'
import type { TFunction } from 'i18next'

function emptyPlaceholder() {
  return <span className="text-[color:var(--text-muted)]">—</span>
}

function SectionTitle({ children }: { children: string }) {
  return <div className="text-xs font-medium text-[color:var(--text-secondary)]">{children}</div>
}

function TableShell({ children }: { children: ReactNode }) {
  return (
    <div className="overflow-x-auto rounded-md border border-[color:var(--bg-card-border)] bg-[color:var(--bg-card)]">
      {children}
    </div>
  )
}

function BaseTable({ children }: { children: ReactNode }) {
  return <table className="min-w-full text-sm">{children}</table>
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function formatValue(value: unknown): string {
  if (value === null) return 'null'
  if (value === undefined) return 'undefined'
  if (typeof value === 'string') return value
  if (typeof value === 'number' || typeof value === 'boolean' || typeof value === 'bigint') return String(value)
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}

type RawKvRow = {
  key?: string
  key_normalized?: string
  value?: string
  source?: string
}

type RawTable = {
  name?: string
  source?: string
  headers?: string[]
  rows?: unknown[][]
}

function isRawKvRow(value: unknown): value is RawKvRow {
  if (!isPlainObject(value)) return false
  return (
    typeof value.key === 'string' ||
    typeof value.key_normalized === 'string' ||
    typeof value.value === 'string' ||
    typeof value.source === 'string'
  )
}

function isRawTable(value: unknown): value is RawTable {
  if (!isPlainObject(value)) return false
  const rows = value.rows
  return Array.isArray(rows)
}

type Props = {
  rawSignalsPretty: string
  t: TFunction
}

export function RawSignalsTable({ rawSignalsPretty, t }: Props) {
  const parsed = useMemo((): unknown => {
    if (!rawSignalsPretty) return null
    try {
      return JSON.parse(rawSignalsPretty)
    } catch {
      return null
    }
  }, [rawSignalsPretty])

  if (!parsed || !isPlainObject(parsed)) {
    return <div className="text-sm text-[color:var(--text-secondary)]">{t('order.detail.rawSignalsEmpty')}</div>
  }

  const entries = Object.entries(parsed)
  if (!entries.length) {
    return <div className="text-sm text-[color:var(--text-secondary)]">{t('order.detail.rawSignalsEmpty')}</div>
  }

  const rawKv = parsed.raw_kv
  const rawTables = parsed.raw_tables

  const rawKvRows: RawKvRow[] = Array.isArray(rawKv) ? rawKv.filter(isRawKvRow) : []
  const rawTableRows: RawTable[] = Array.isArray(rawTables) ? rawTables.filter(isRawTable) : []

  const restEntries = entries.filter(([key]) => key !== 'raw_kv' && key !== 'raw_tables')

  return (
    <div className="space-y-4">
      {rawKvRows.length ? (
        <div className="space-y-2">
          <SectionTitle>raw_kv</SectionTitle>
          <TableShell>
            <BaseTable>
              <thead className="text-left">
                <tr className="table-divider-strong">
                  <th className="py-2 pr-4 whitespace-nowrap w-[14rem]">Key</th>
                  <th className="py-2 pr-4 whitespace-nowrap w-[12rem]">Normalized</th>
                  <th className="py-2 pr-4">Value</th>
                  <th className="py-2 pr-4 whitespace-nowrap w-[10rem]">Source</th>
                </tr>
              </thead>
              <tbody>
                {rawKvRows.map((row, idx) => (
                  <tr key={`${row.key ?? 'key'}-${idx}`} className="table-divider">
                    <td
                      className="py-2 pr-4 align-top font-mono text-xs whitespace-nowrap max-w-[14rem] truncate"
                      title={row.key ?? ''}
                    >
                      {row.key ?? emptyPlaceholder()}
                    </td>
                    <td
                      className="py-2 pr-4 align-top font-mono text-xs whitespace-nowrap max-w-[12rem] truncate"
                      title={row.key_normalized ?? ''}
                    >
                      {row.key_normalized ? row.key_normalized : emptyPlaceholder()}
                    </td>
                    <td className="py-2 pr-4 align-top">
                      {row.value ? (
                        <div className="font-mono text-xs whitespace-pre-wrap break-words">{row.value}</div>
                      ) : (
                        emptyPlaceholder()
                      )}
                    </td>
                    <td className="py-2 pr-4 align-top text-xs whitespace-nowrap">
                      {row.source ? row.source : emptyPlaceholder()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </BaseTable>
          </TableShell>
        </div>
      ) : null}

      {rawTableRows.length ? (
        <div className="space-y-4">
          <SectionTitle>raw_tables</SectionTitle>
          {rawTableRows.map((tbl, idx) => {
            const headers = Array.isArray(tbl.headers) ? tbl.headers : []
            const rows = Array.isArray(tbl.rows) ? tbl.rows : []
            const title = tbl.name ? `${tbl.name}${tbl.source ? ` (${tbl.source})` : ''}` : `table_${idx}`
            return (
              <div key={`${tbl.name ?? 'table'}-${idx}`} className="space-y-2">
                <div className="text-xs font-medium text-[color:var(--text-secondary)]">{title}</div>
                <TableShell>
                  <BaseTable>
                    {headers.length ? (
                      <thead className="text-left">
                        <tr className="table-divider-strong">
                          {headers.map(h => (
                            <th key={h} className="py-2 pr-4 whitespace-nowrap">
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                    ) : null}
                    <tbody>
                      {rows.map((r, rIdx) => (
                        <tr key={rIdx} className="table-divider">
                          {Array.isArray(r)
                            ? r.map((cell, cIdx) => (
                                <td key={cIdx} className="py-2 pr-4 align-top">
                                  <div className="font-mono text-xs whitespace-pre-wrap break-words">
                                    {formatValue(cell)}
                                  </div>
                                </td>
                              ))
                            : null}
                        </tr>
                      ))}
                    </tbody>
                  </BaseTable>
                </TableShell>
              </div>
            )
          })}
        </div>
      ) : null}

      {restEntries.length ? (
        <div className="space-y-2">
          <SectionTitle>other</SectionTitle>
          <TableShell>
            <BaseTable>
              <thead className="text-left">
                <tr className="table-divider-strong">
                  <th className="py-2 pr-4 whitespace-nowrap w-[14rem]">Key</th>
                  <th className="py-2 pr-4">Value</th>
                </tr>
              </thead>
              <tbody>
                {restEntries.map(([key, value]) => (
                  <tr key={key} className="table-divider">
                    <td className="py-2 pr-4 align-top font-mono text-xs whitespace-nowrap">{key}</td>
                    <td className="py-2 pr-4 align-top">
                      <div className="font-mono text-xs whitespace-pre-wrap break-all">{formatValue(value)}</div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </BaseTable>
          </TableShell>
        </div>
      ) : null}
    </div>
  )
}
