import { useEffect, useState } from 'react'
import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom'
import type { Session } from '@supabase/supabase-js'
import { supabase } from './lib/supabase'
import { ThemeProvider } from './components/ThemeProvider'
import { useAppTranslation, I18N_SCOPES } from './lib/i18n'
import LoginDialog from './components/LoginDialog'
import Layout from './components/Layout'
import DashboardPage from './pages/DashboardPage'
import ExtractionsPage from './pages/ExtractionsPage'
import ExtractionDetailPage from './pages/ExtractionDetailPage'
import OrdersPage from './pages/OrdersPage'
import OrderDetailPage from './pages/OrderDetailPage'
import ErrorPage from './components/ErrorPage'
import { UiMessagesProvider } from './ui/messages/UiMessagesProvider'
import SuccessToastOverlay from './components/messages/SuccessToastOverlay'
import './lib/i18n' // Initialize i18n

function App() {
  const { t } = useAppTranslation(I18N_SCOPES.extraction)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setLoading(false)
    })

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
    })

    return () => subscription.unsubscribe()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-slate-300"></div>
      </div>
    )
  }

  if (!session) {
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
      element: <Layout user={session.user} pageTitle={t('extraction.title')} />,
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
