import { useCallback, useEffect, useMemo, useState } from 'react'
import { useLocation, useOutletContext } from 'react-router-dom'
import { useAppTranslation, I18N_SCOPES } from '../lib/i18n'
import { services } from '../services'
import type { ExtractionListQuery, ExtractionRow, ExtractionStatus } from '../services/core/extraction/types'
import { useUiMessages } from '../ui/messages/UiMessagesContext'
import { createErrorMessage } from '../ui/messages/fromError'
import { PageHeader } from '../components/layout/PageHeader'
import { isAllowedStatusFilter, useExtractionsPageState } from './extractions/useExtractionsPageState'
import { ExtractionStatusCards } from './extractions/ExtractionStatusCards'
import { ExtractionsTable } from './extractions/ExtractionsTable'
import {
  loadExtractionsPagePersistedState,
  useExtractionsPagePersistence,
} from './extractions/useExtractionsPagePersistence'
import { useExtractionsPageMutations } from './extractions/useExtractionsPageMutations'
import { useLoadPagedRows, useLoadStatusCounts, useStatusFilterFromUrl } from './shared/useListPageData'
import type { AuthSessionUser } from '../services/core/auth/types'

export default function ExtractionsPage() {
  const { t, i18n } = useAppTranslation(I18N_SCOPES.extraction)
  const { push } = useUiMessages()
  const location = useLocation()
  const outlet = useOutletContext<{ user: AuthSessionUser }>()

  const hasStatusParam = Boolean(new URLSearchParams(location.search).get('status')?.trim())
  const persisted = hasStatusParam ? null : loadExtractionsPagePersistedState('xscanner:studio:extractionsPage:v1')

  const { state, actions, derived } = useExtractionsPageState(persisted?.state ?? undefined)

  const [loading, setLoading] = useState(true)
  const [rows, setRows] = useState<ExtractionRow[]>([])
  const [total, setTotal] = useState(0)

  const [counts, setCounts] = useState<{
    pending: number
    corrected: number
    validated: number
    rejected: number
    error: number
  } | null>(null)
  const [countsBusy, setCountsBusy] = useState(false)

  useStatusFilterFromUrl({
    search: location.search,
    isAllowed: isAllowedStatusFilter,
    setStatusFilters: actions.setStatusFilters,
  })

  useEffect(() => {
    if (location.hash === '#table') {
      requestAnimationFrame(() => {
        document.getElementById('extractions-table')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      })
    }
  }, [location.hash])

  useExtractionsPagePersistence({
    storageKey: 'xscanner:studio:extractionsPage:v1',
    state,
    initialScrollY: persisted?.scrollY ?? null,
    restoreScrollWhen: !loading,
    skipScrollRestore: location.hash === '#table',
  })

  const countsFilters = useMemo(
    () => ({
      search: state.search,
      createdAtFrom: state.createdAtFrom.trim() ? state.createdAtFrom : undefined,
      createdAtTo: state.createdAtTo.trim() ? state.createdAtTo : undefined,
    }),
    [state.createdAtFrom, state.createdAtTo, state.search]
  )

  const query: ExtractionListQuery = useMemo(
    () => ({
      page: state.page,
      pageSize: state.pageSize,
      sort: state.sort,
      search: state.search,
      createdAtFrom: state.createdAtFrom.trim() ? state.createdAtFrom : undefined,
      createdAtTo: state.createdAtTo.trim() ? state.createdAtTo : undefined,
      statuses: state.statusFilters.length > 0 ? state.statusFilters : undefined,
    }),
    [state.createdAtFrom, state.createdAtTo, state.page, state.pageSize, state.search, state.sort, state.statusFilters]
  )

  const onError = useCallback(
    (error: unknown) => {
      push(createErrorMessage(t, error))
    },
    [push, t]
  )

  useLoadPagedRows({
    query,
    refreshKey: state.refreshKey,
    load: services.extractionService.listActivePaged,
    onError,
    setLoading,
    setRows,
    setTotal,
  })

  useLoadStatusCounts({
    filters: countsFilters,
    refreshKey: state.refreshKey,
    load: services.extractionService.getActiveStatusCounts,
    onError,
    setBusy: setCountsBusy,
    setCounts,
  })

  const { onRegister, onReject, onRejectMany } = useExtractionsPageMutations({
    userId: outlet.user.id,
    t,
    push,
    query,
    statusFilters: state.statusFilters,
    countsFilters,
    setLoading,
    setCountsBusy,
    setRows,
    setTotal,
    setCounts,
  })

  const onToggleStatusCard = useCallback(
    (status: ExtractionStatus) => {
      actions.toggleStatusFilter(status)
    },
    [actions]
  )

  const clearAllFilters = useCallback(() => {
    actions.clearFilters()
  }, [actions])

  return (
    <div>
      <PageHeader
        title={t('extraction.list.title')}
        subtitle={t('extraction.list.subtitle')}
        backLabel={t('common.action.back')}
      />

      <ExtractionStatusCards
        counts={counts}
        busy={countsBusy}
        activeFilters={state.statusFilters}
        onToggle={onToggleStatusCard}
        labels={{
          pending: t('extraction.list.stats.pending'),
          corrected: t('extraction.list.stats.corrected'),
          validated: t('extraction.list.stats.validated'),
          rejected: t('extraction.list.stats.rejected'),
          error: t('extraction.list.stats.errors'),
        }}
      />

      <div id="extractions-table" className="panel">
        <ExtractionsTable
          rows={rows}
          total={total}
          loading={loading}
          t={t}
          language={i18n.language}
          sort={state.sort}
          onSortChange={actions.setSort}
          searchInput={state.searchInput}
          onSearchInputChange={actions.setSearchInput}
          showFilters={state.showFilters}
          onToggleFilters={actions.toggleFilters}
          onClearFilters={clearAllFilters}
          hasAnyFilter={derived.hasAnyFilter}
          createdAtFrom={state.createdAtFrom}
          createdAtTo={state.createdAtTo}
          onDateRangeChange={actions.setDateRange}
          statusFilters={state.statusFilters}
          onStatusFiltersChange={actions.setStatusFilters}
          page={state.page}
          pageSize={state.pageSize}
          onPageChange={actions.setPage}
          onPageSizeChange={nextSize => actions.setPageSize(nextSize)}
          onRegister={originalId => void onRegister(originalId)}
          onReject={originalId => void onReject(originalId)}
          onRejectMany={onRejectMany}
        />
      </div>
    </div>
  )
}
