import { useNavigate, useRouteError } from 'react-router-dom'
import { useAppTranslation, I18N_SCOPES } from '../lib/i18n'
import { getUserFacingErrorMessage } from '../lib/utils/errors'
import { useContextSensitiveBack } from '../lib/router/useContextSensitiveBack'

export default function ErrorPage() {
  const { t } = useAppTranslation(I18N_SCOPES.common)
  const navigate = useNavigate()
  const goBack = useContextSensitiveBack('/')
  const error = useRouteError()

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="max-w-md w-full p-8 text-center">
        {/* Error Icon */}
        <div className="mb-8 flex justify-center">
          <div className="relative">
            <div className="absolute inset-0 bg-red-500/20 blur-3xl rounded-full"></div>
            <div className="relative w-24 h-24 bg-gradient-to-br from-red-500 to-orange-500 rounded-full flex items-center justify-center shadow-2xl">
              <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>
          </div>
        </div>

        {/* Error Message */}
        <div className="flex items-center justify-center gap-3 mb-4">
          <button
            type="button"
            aria-label={t('common.error.goBack')}
            onClick={goBack}
            className="inline-flex items-center justify-center w-10 h-10 rounded-lg bg-white/10 text-white hover:bg-white/20 transition-all duration-200"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <h1 className="text-3xl font-bold text-white">Oops!</h1>
        </div>
        <p className="text-gray-300 mb-2">{t('common.error.title')}</p>
        <p className="text-gray-400 text-sm mb-8">{getUserFacingErrorMessage(t, error)}</p>

        {/* Actions */}
        <div className="flex flex-col gap-3">
          <button
            onClick={() => navigate('/')}
            className="px-6 py-3 bg-white/10 text-white font-semibold rounded-lg hover:bg-white/20 transition-all duration-200"
          >
            {t('common.error.goHome')}
          </button>
        </div>

        {/* Decorative Elements */}
        <div className="absolute inset-0 pointer-events-none">
          <div
            className="absolute rounded-full mix-blend-multiply filter blur-xl opacity-20 -top-4 -left-4 w-72 h-72 animate-blob"
            style={{ backgroundColor: 'rgba(239, 68, 68, 0.3)' }}
          />
          <div
            className="absolute rounded-full mix-blend-multiply filter blur-xl opacity-20 -top-4 -right-4 w-72 h-72 animate-blob"
            style={{ backgroundColor: 'rgba(249, 115, 22, 0.3)', animationDelay: '2s' }}
          />
        </div>
      </div>
    </div>
  )
}
