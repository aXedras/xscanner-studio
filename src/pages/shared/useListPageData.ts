import { useEffect } from 'react'

export function useStatusFilterFromUrl<TStatus extends string>(params: {
  search: string
  isAllowed: (value: string | null) => value is TStatus
  setStatusFilters: (value: TStatus[]) => void
}) {
  const { search, isAllowed, setStatusFilters } = params

  useEffect(() => {
    const status = new URLSearchParams(search).get('status')?.trim() ?? null
    if (isAllowed(status)) setStatusFilters([status])
  }, [isAllowed, search, setStatusFilters])
}

type PagedResult<TRow> = {
  items: TRow[]
  total: number
}

export function useLoadPagedRows<TQuery, TRow>(params: {
  query: TQuery
  refreshKey: number
  load: (query: TQuery) => Promise<PagedResult<TRow>>
  onError: (error: unknown) => void
  setLoading: (value: boolean) => void
  setRows: (value: TRow[]) => void
  setTotal: (value: number) => void
}) {
  const { query, refreshKey, load, onError, setLoading, setRows, setTotal } = params

  useEffect(() => {
    let isMounted = true

    const run = async () => {
      setLoading(true)
      try {
        const result = await load(query)
        if (!isMounted) return
        setRows(result.items)
        setTotal(result.total)
      } catch (error) {
        onError(error)
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    run()
    return () => {
      isMounted = false
    }
  }, [load, onError, query, refreshKey, setLoading, setRows, setTotal])
}

export function useLoadStatusCounts<TFilters, TCounts>(params: {
  filters: TFilters
  refreshKey: number
  load: (filters: TFilters) => Promise<TCounts>
  onError: (error: unknown) => void
  setBusy: (value: boolean) => void
  setCounts: (value: TCounts) => void
}) {
  const { filters, refreshKey, load, onError, setBusy, setCounts } = params

  useEffect(() => {
    let isMounted = true

    const run = async () => {
      setBusy(true)
      try {
        const nextCounts = await load(filters)
        if (!isMounted) return
        setCounts(nextCounts)
      } catch (error) {
        onError(error)
      } finally {
        if (isMounted) setBusy(false)
      }
    }

    run()
    return () => {
      isMounted = false
    }
  }, [filters, load, onError, refreshKey, setBusy, setCounts])
}
