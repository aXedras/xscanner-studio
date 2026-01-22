import { useEffect, useMemo, useState } from 'react'
import { useAppTranslation, I18N_SCOPES } from '../lib/i18n'
import { Link, useNavigate } from 'react-router-dom'
import { UploadAndExtractPanel } from '../components/extractions/UploadAndExtractPanel'
import { services } from '../services'
import { useUiMessages } from '../ui/messages/UiMessagesContext'
import { createErrorMessage } from '../ui/messages/fromError'
import type { ExtractionStatus } from '../services/core/extraction/types'
import {
  StatIconError,
  StatIconPending,
  StatIconRejected,
  StatIconTotal,
  StatIconValidated,
} from '../components/ui/StatCardIcons'

export default function DashboardPage() {
  const { t } = useAppTranslation(I18N_SCOPES.extraction)
  const navigate = useNavigate()
  const { push } = useUiMessages()

  const [countsLoading, setCountsLoading] = useState(true)
  const [counts, setCounts] = useState({ pending: 0, corrected: 0, validated: 0, rejected: 0, error: 0 })

  const total = useMemo(
    () => counts.pending + counts.corrected + counts.validated + counts.rejected + counts.error,
    [counts]
  )

  useEffect(() => {
    let isMounted = true

    const run = async () => {
      setCountsLoading(true)
      try {
        const nextCounts = await services.extractionService.getActiveStatusCounts({})
        if (!isMounted) return
        setCounts(nextCounts)
      } catch (error) {
        push(createErrorMessage(t, error))
      } finally {
        if (isMounted) setCountsLoading(false)
      }
    }

    run()
    return () => {
      isMounted = false
    }
  }, [push, t])

  const goToExtractions = (status?: ExtractionStatus) => {
    const url = status ? `/extractions?status=${encodeURIComponent(status)}#table` : '/extractions#table'
    navigate(url)
  }

  return (
    <div>
      {/* Welcome Hero */}
      <div className="mb-12">
        <h1 className="text-heading text-heading-gold mb-3">{t('extraction.welcome.title')}</h1>
        <p className="text-subtitle">{t('extraction.welcome.subtitle')}</p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6 mb-12">
        <button type="button" className="stat-card text-left" onClick={() => goToExtractions()}>
          <StatIconTotal />
          <div className="stat-content">
            <p className="stat-label">{t('extraction.stats.total')}</p>
            <p className="stat-value stat-value-gold">{countsLoading ? '—' : total}</p>
          </div>
        </button>

        <button type="button" className="stat-card text-left" onClick={() => goToExtractions('pending')}>
          <StatIconPending />
          <div className="stat-content">
            <p className="stat-label">{t('extraction.stats.pending')}</p>
            <p className="stat-value stat-value-orange">{countsLoading ? '—' : counts.pending}</p>
          </div>
        </button>

        <button type="button" className="stat-card text-left" onClick={() => goToExtractions('validated')}>
          <StatIconValidated />
          <div className="stat-content">
            <p className="stat-label">{t('extraction.stats.validated')}</p>
            <p className="stat-value stat-value-green">{countsLoading ? '—' : counts.validated}</p>
          </div>
        </button>

        <button type="button" className="stat-card text-left" onClick={() => goToExtractions('rejected')}>
          <StatIconRejected />
          <div className="stat-content">
            <p className="stat-label">{t('extraction.list.stats.rejected')}</p>
            <p className="stat-value stat-value-red">{countsLoading ? '—' : counts.rejected}</p>
          </div>
        </button>

        <button type="button" className="stat-card text-left" onClick={() => goToExtractions('error')}>
          <StatIconError />
          <div className="stat-content">
            <p className="stat-label">{t('extraction.stats.errors')}</p>
            <p className="stat-value stat-value-red">{countsLoading ? '—' : counts.error}</p>
          </div>
        </button>
      </div>

      {/* Action Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-12">
        <UploadAndExtractPanel />

        <div className="panel">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-teal-500 rounded-full flex items-center justify-center flex-shrink-0 shadow-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <div>
              <h3 className="text-body font-bold mb-1">{t('extraction.history.title')}</h3>
              <p className="text-label">{t('extraction.history.description')}</p>
            </div>
          </div>
          <Link to="/extractions" className="btn w-full">
            {t('extraction.history.action')}
          </Link>
        </div>
      </div>
    </div>
  )
}
