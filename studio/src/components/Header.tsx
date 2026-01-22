import LanguageSwitcher from './LanguageSwitcher'
import ThemeSwitcher from './ThemeSwitcher'
import type { User } from '@supabase/supabase-js'
import { Link } from 'react-router-dom'
import { useAppTranslation, I18N_SCOPES } from '../lib/i18n'
import { TopNavigation } from './layout/TopNavigation'

interface HeaderProps {
  user: User
  title: string
  onSignOut: () => void
  logoutLabel: string
}

export default function Header({ user, title, onSignOut, logoutLabel }: HeaderProps) {
  const { t } = useAppTranslation(I18N_SCOPES.common)

  return (
    <nav className="nav">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-[1fr_auto_1fr] items-center h-16 gap-4">
          <div className="flex items-center gap-6 min-w-0">
            <Link to="/" className="flex items-end gap-3" aria-label="Home">
              <div className="logo-container">
                <img src="/axedras-logo.svg" alt="aXedras Logo" className="h-8 w-auto logo-light" />
                <img src="/axedras-logo-dark.svg" alt="aXedras Logo" className="h-8 w-auto logo-dark" />
              </div>
              <span className="text-xl font-bold text-heading-gold">{title}</span>
            </Link>
          </div>

          <div className="hidden sm:flex justify-center">
            <TopNavigation t={t} />
          </div>

          <div className="flex items-center gap-3 justify-self-end">
            <LanguageSwitcher />
            <ThemeSwitcher />
            <div className="badge">
              <div className="icon-active animate-pulse"></div>
              <span>{user.user_metadata?.display_name || user.email}</span>
            </div>
            <button onClick={onSignOut} className="btn btn-outline btn-icon" aria-label={logoutLabel}>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </nav>
  )
}
