import { useEffect, useState } from 'react'
import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom'
import { ThemeProvider } from './components/ThemeProvider'
import { useAppTranslation, I18N_SCOPES } from './lib/i18n'
import LoginDialog from './components/LoginDialog'
import Layout from './components/Layout'
import DashboardPage from './pages/DashboardPage'
import ExtractionsPage from './pages/ExtractionsPage'
import ExtractionDetailPage from './pages/ExtractionDetailPage'
import OrdersPage from './pages/OrdersPage'
import OrderDetailPage from './pages/OrderDetailPage'
import SettingsPage from './pages/SettingsPage'
import ErrorPage from './components/ErrorPage'
import { UiMessagesProvider } from './ui/messages/UiMessagesProvider'
import SuccessToastOverlay from './components/messages/SuccessToastOverlay'
import { services } from './services'
import { AUTH_SESSION_CHANGED_EVENT } from './services/core/auth/events'
import type { AuthSessionUser } from './services/core/auth/types'
import { DEFAULT_API_BASE_URL, setApiBaseUrlOverride } from './lib/runtimeEnv'
import './lib/i18n' // Initialize i18n

type BootstrapState = 'loading' | 'ready' | 'error'

function App() {
  const { t } = useAppTranslation(I18N_SCOPES.extraction)
  const { t: tCommon } = useAppTranslation(I18N_SCOPES.common)
  const [user, setUser] = useState<AuthSessionUser | null>(null)
  const [bootstrapState, setBootstrapState] = useState<BootstrapState>('loading')
  const [sessionErrorMessage, setSessionErrorMessage] = useState<string | null>(null)

  useEffect(() => {
    let isMounted = true

    const refreshSession = async () => {
      try {
        const result = await services.authService.getSession()
        if (!isMounted) return
        setUser(result.session)
        setSessionErrorMessage(null)
        setBootstrapState('ready')
      } catch (error) {
        if (!isMounted) return
        const message = error instanceof Error ? error.message : 'Unknown auth session error'
        setUser(null)
        setSessionErrorMessage(message)
        setBootstrapState('error')
      }
    }

    const onAuthSessionChanged = () => {
      void refreshSession()
    }

    const onVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        void refreshSession()
      }
    }

    void refreshSession()
    globalThis.addEventListener(AUTH_SESSION_CHANGED_EVENT, onAuthSessionChanged)
    document.addEventListener('visibilitychange', onVisibilityChange)

    return () => {
      isMounted = false
      globalThis.removeEventListener(AUTH_SESSION_CHANGED_EVENT, onAuthSessionChanged)
      document.removeEventListener('visibilitychange', onVisibilityChange)
    }
  }, [])

  if (bootstrapState === 'loading') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-slate-300"></div>
      </div>
    )
  }

  if (bootstrapState === 'error') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center px-6">
        <div className="max-w-xl w-full p-6 rounded-xl bg-white/10 text-white border border-white/20">
          <h1 className="text-xl font-semibold mb-2">{tCommon('common.error.title')}</h1>
          <p className="text-sm text-slate-200 mb-4">{sessionErrorMessage ?? 'Session bootstrap failed.'}</p>
          <button
            type="button"
            onClick={() => {
              setBootstrapState('loading')
              setSessionErrorMessage(null)
              globalThis.dispatchEvent(new Event(AUTH_SESSION_CHANGED_EVENT))
            }}
            className="btn btn-outline"
          >
            {tCommon('common.action.retry')}
          </button>
          <button
            type="button"
            onClick={() => {
              setApiBaseUrlOverride(DEFAULT_API_BASE_URL)
              globalThis.location.reload()
            }}
            className="btn btn-outline ml-2"
          >
            {tCommon('common.settings.recoverDefaultApi')}
          </button>
        </div>
      </div>
    )
  }

  if (!user) {
    return (
      <ThemeProvider defaultTheme="light">
        <UiMessagesProvider>
          <SuccessToastOverlay closeLabel={t('common.action.close')} />
          <LoginDialog />
        </UiMessagesProvider>
      </ThemeProvider>
    )
  }

  // Create router with user context
  const router = createBrowserRouter([
    {
      path: '/',
      element: <Layout user={user} pageTitle={t('extraction.title')} />,
      errorElement: <ErrorPage />,
      children: [
        {
          index: true,
          element: <DashboardPage />,
        },
        {
          path: 'extractions',
          element: <ExtractionsPage />,
        },
        {
          path: 'extractions/:originalId',
          element: <ExtractionDetailPage />,
        },
        {
          path: 'orders',
          element: <OrdersPage />,
        },
        {
          path: 'orders/:originalId',
          element: <OrderDetailPage />,
        },
        {
          path: 'settings',
          element: <SettingsPage />,
        },
      ],
    },
    {
      path: '*',
      element: <Navigate to="/" replace />,
    },
  ])

  return (
    <ThemeProvider defaultTheme="light">
      <UiMessagesProvider>
        <SuccessToastOverlay closeLabel={t('common.action.close')} />
        <RouterProvider router={router} />
      </UiMessagesProvider>
    </ThemeProvider>
  )
}

export default App
