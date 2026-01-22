import { useEffect, useMemo, useState } from 'react'
import { services } from '../../services'
import type { BilRegistrationRow, ExtractionRow } from '../../services/core/extraction/types'

function groupByExtractionId(rows: BilRegistrationRow[]): Record<string, BilRegistrationRow[]> {
  const map: Record<string, BilRegistrationRow[]> = {}
  for (const row of rows) {
    const key = row.extraction_id
    if (!map[key]) map[key] = []
    map[key].push(row)
  }
  for (const key of Object.keys(map)) {
    map[key].sort((a, b) => (a.created_at < b.created_at ? 1 : a.created_at > b.created_at ? -1 : 0))
  }
  return map
}

export function useBilRegistrationState(input: { versions: ExtractionRow[]; activeId: string | null }) {
  const extractionIds = useMemo(() => input.versions.map(v => String(v.id)), [input.versions])

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [byExtractionId, setByExtractionId] = useState<Record<string, BilRegistrationRow[]>>({})
  const [selectedExtractionId, setSelectedExtractionId] = useState<string | null>(null)
  const [certificateId, setCertificateId] = useState<string | null>(null)

  useEffect(() => {
    // Details should open on click; default to no selection.
    setSelectedExtractionId(null)
  }, [extractionIds, input.activeId])

  useEffect(() => {
    let isMounted = true

    const run = async () => {
      setLoading(true)
      setError(null)
      try {
        const rows = await services.bilService.listRegistrationsByExtractionIds(extractionIds)
        if (!isMounted) return
        setByExtractionId(groupByExtractionId(rows))
        const latestSuccess = rows.find(r => r.success && r.certificate_id)
        setCertificateId(latestSuccess?.certificate_id ?? null)
      } catch (e) {
        if (!isMounted) return
        const message = e instanceof Error ? e.message : String(e)
        setError(message)
        setByExtractionId({})
        setCertificateId(null)
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    if (extractionIds.length === 0) {
      setByExtractionId({})
      setError(null)
      setLoading(false)
      setCertificateId(null)
      return () => {
        isMounted = false
      }
    }

    run()
    return () => {
      isMounted = false
    }
  }, [extractionIds])

  const selectedAttempts = useMemo(() => {
    if (!selectedExtractionId) return []
    return byExtractionId[selectedExtractionId] ?? []
  }, [byExtractionId, selectedExtractionId])

  return {
    loading,
    error,
    byExtractionId,
    selectedExtractionId,
    setSelectedExtractionId,
    selectedAttempts,
    certificateId,
  }
}
