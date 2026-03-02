import { Outlet } from 'react-router-dom'
import { useAppTranslation, I18N_SCOPES } from '../lib/i18n'
import Header from './Header'
import Footer from './Footer'
import MessageCenter from './messages/MessageCenter'
import { useUiMessages } from '../ui/messages/UiMessagesContext'
import { createErrorMessage } from '../ui/messages/fromError'
import ContentContainer from './layout/ContentContainer'
import { NavigationHistoryProvider } from '../lib/router/NavigationHistoryProvider'
import { services } from '../services'
import type { AuthSessionUser } from '../services/core/auth/types'

interface LayoutProps {
  user: AuthSessionUser
  pageTitle: string
}

export default function Layout({ user, pageTitle }: LayoutProps) {
  const { t } = useAppTranslation(I18N_SCOPES.auth)
  const { push } = useUiMessages()

  const handleSignOut = async () => {
    try {
      await services.authService.signOut()
    } catch (error) {
      push(createErrorMessage(t, error))
    }
  }

  return (
    <div className="app-layout">
      <Header user={user} title={pageTitle} onSignOut={handleSignOut} logoutLabel={t('auth.logout')} />

      <main className="content">
        <NavigationHistoryProvider>
          <ContentContainer>
            <div className="mb-4">
              <MessageCenter closeLabel={t('common.action.close')} />
            </div>
            <Outlet context={{ user }} />
          </ContentContainer>
        </NavigationHistoryProvider>
      </main>

      <Footer />
    </div>
  )
}
