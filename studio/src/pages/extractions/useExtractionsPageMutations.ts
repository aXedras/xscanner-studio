import { useCallback } from 'react'
import type { Dispatch, SetStateAction } from 'react'
import type { TFunction } from 'i18next'
import { runWithConcurrency } from '../../lib/utils/concurrency'
import { services } from '../../services'
import { createErrorMessage } from '../../ui/messages/fromError'
import type { UiMessagesApi } from '../../ui/messages/UiMessagesContext'
import type { ExtractionListQuery, ExtractionRow, ExtractionStatus } from '../../services/core/extraction/types'

type StatusCounts = {
  pending: number
  corrected: number
  validated: number
  rejected: number
  error: number
}

type Args = {
  userId: string
  t: TFunction
  push: UiMessagesApi['push']

  query: ExtractionListQuery
  statusFilters: ExtractionStatus[]
  countsFilters: {
    search: string
    createdAtFrom?: string
    createdAtTo?: string
  }

  setLoading: (value: boolean) => void
  setCountsBusy: (value: boolean) => void
  setRows: Dispatch<SetStateAction<ExtractionRow[]>>
  setTotal: Dispatch<SetStateAction<number>>
  setCounts: Dispatch<SetStateAction<StatusCounts | null>>
}

export function useExtractionsPageMutations({
  userId,
  t,
  push,
  query,
  statusFilters,
  countsFilters,
  setLoading,
  setCountsBusy,
  setRows,
  setTotal,
  setCounts,
}: Args) {
  const applyLocalStatusUpdate = useCallback(
    (originalId: string, nextStatus: ExtractionStatus) => {
      let previousStatus: ExtractionStatus | null = null

      setRows(prevRows => {
        const current = prevRows.find(r => String(r.original_id) === String(originalId))
        if (!current) return prevRows

        previousStatus = current.status

        const updated = prevRows.map(r =>
          String(r.original_id) === String(originalId)
            ? {
                ...r,
                status: nextStatus,
              }
            : r
        )

        if (statusFilters.length > 0 && !statusFilters.includes(nextStatus)) {
          return updated.filter(r => String(r.original_id) !== String(originalId))
        }

        return updated
      })

      setTotal(prevTotal => {
        if (statusFilters.length === 0) return prevTotal
        if (statusFilters.includes(nextStatus)) return prevTotal
        return Math.max(0, prevTotal - 1)
      })

      setCounts(prev => {
        if (!prev) return prev

        const next = { ...prev }

        const dec = (key: keyof typeof next) => {
          next[key] = Math.max(0, next[key] - 1)
        }

        const inc = (key: keyof typeof next) => {
          next[key] = next[key] + 1
        }

        const mapKey = (status: ExtractionStatus): keyof typeof next => {
          if (status === 'pending') return 'pending'
          if (status === 'corrected') return 'corrected'
          if (status === 'validated') return 'validated'
          if (status === 'rejected') return 'rejected'
          return 'error'
        }

        if (previousStatus) dec(mapKey(previousStatus))
        inc(mapKey(nextStatus))
        return next
      })
    },
    [setCounts, setRows, setTotal, statusFilters]
  )

  const onRegister = useCallback(
    async (originalId: string) => {
      try {
        await services.extractionService.validateActive({ originalId, updatedBy: userId })
        push({
          variant: 'success',
          title: t('common.toast.update.title'),
          description: t('common.toast.update.description'),
        })
        applyLocalStatusUpdate(originalId, 'validated')
      } catch (error) {
        push(createErrorMessage(t, error))
      }
    },
    [applyLocalStatusUpdate, push, t, userId]
  )

  const onReject = useCallback(
    async (originalId: string) => {
      try {
        await services.extractionService.rejectActive({ originalId, updatedBy: userId })
        push({
          variant: 'success',
          title: t('common.toast.update.title'),
          description: t('common.toast.update.description'),
        })
        applyLocalStatusUpdate(originalId, 'rejected')
      } catch (error) {
        push(createErrorMessage(t, error))
      }
    },
    [applyLocalStatusUpdate, push, t, userId]
  )

  const onRejectMany = useCallback(
    async (originalIds: string[]) => {
      const ok: string[] = []
      const failed: Array<{ id: string; error: unknown }> = []

      await runWithConcurrency(originalIds, 4, async originalId => {
        try {
          await services.extractionService.rejectActive({ originalId, updatedBy: userId })
          ok.push(originalId)
          applyLocalStatusUpdate(originalId, 'rejected')
        } catch (error) {
          failed.push({ id: originalId, error })
        }
      })

      if (ok.length > 0) {
        push({
          variant: 'success',
          title: t('common.toast.bulkReject.title'),
          description: t('common.toast.bulkReject.description', { count: ok.length }),
        })
      }

      if (failed.length > 0) {
        push({
          variant: 'error',
          title: t('common.toast.error.title'),
          description: t('common.toast.bulkRejectFailed.description', { count: failed.length }),
        })
      }

      if (ok.length > 0) {
        setLoading(true)
        setCountsBusy(true)
        try {
          const [result, nextCounts] = await Promise.all([
            services.extractionService.listActivePaged(query),
            services.extractionService.getActiveStatusCounts(countsFilters),
          ])
          setRows(result.items)
          setTotal(result.total)
          setCounts(nextCounts)
        } catch (error) {
          push(createErrorMessage(t, error))
        } finally {
          setLoading(false)
          setCountsBusy(false)
        }
      }

      return { ok, failed }
    },
    [
      applyLocalStatusUpdate,
      countsFilters,
      push,
      query,
      setCounts,
      setCountsBusy,
      setLoading,
      setRows,
      setTotal,
      t,
      userId,
    ]
  )

  return { onRegister, onReject, onRejectMany }
}
