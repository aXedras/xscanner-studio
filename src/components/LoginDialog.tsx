import { useCallback, useMemo, useState } from 'react'
import { useAppTranslation, I18N_SCOPES } from '../lib/i18n'
import MessageCenter from './messages/MessageCenter'
import { services } from '../services'
import { useUiMessages } from '../ui/messages/UiMessagesContext'
import { createErrorMessage } from '../ui/messages/fromError'

export default function LoginDialog() {
  const { t } = useAppTranslation(I18N_SCOPES.auth)
  const [mode, setMode] = useState<'sign_in' | 'sign_up'>('sign_in')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { push, clear } = useUiMessages()

  const title = useMemo(() => {
    return mode === 'sign_in' ? t('auth.login.subtitle') : t('auth.signup.subtitle')
  }, [mode, t])

  const onSubmit = useCallback(async () => {
    clear()
    setIsSubmitting(true)

    try {
      if (mode === 'sign_in') {
        await services.authService.signIn({ email, password })
        return
      }

      const result = await services.authService.signUp({ email, password, displayName })
      if (!result.hasSession) {
        push({ variant: 'info', description: t('auth.signup.checkEmail') })
      }
    } catch (error) {
      push(createErrorMessage(t, error))
    } finally {
      setIsSubmitting(false)
    }
  }, [mode, email, password, displayName, t, clear, push])

  return (
    <div
      className="min-h-screen flex items-center justify-center"
      style={{ background: 'linear-gradient(to bottom right, var(--bg-secondary), var(--bg-primary))' }}
    >
      <div
        className="absolute inset-0"
        style={{
          backgroundImage:
            'radial-gradient(at 20% 80%, rgba(196, 160, 83, 0.12) 0px, transparent 50%), radial-gradient(at 90% 10%, rgba(92, 184, 92, 0.12) 0px, transparent 50%)',
        }}
      />

      <div className="relative w-full max-w-md">
        <div
          className="absolute rounded-full mix-blend-multiply filter blur-xl opacity-30 -top-4 -left-4 w-72 h-72 animate-blob"
          style={{ backgroundColor: 'rgba(196, 160, 83, 0.2)' }}
        />
        <div
          className="absolute rounded-full mix-blend-multiply filter blur-xl opacity-30 -top-4 -right-4 w-72 h-72 animate-blob"
          style={{ backgroundColor: 'rgba(249, 168, 37, 0.2)', animationDelay: '2s' }}
        />
        <div
          className="absolute rounded-full mix-blend-multiply filter blur-xl opacity-30 -bottom-8 left-20 w-72 h-72 animate-blob"
          style={{ backgroundColor: 'rgba(92, 184, 92, 0.2)', animationDelay: '4s' }}
        />

        <div className="relative backdrop-blur-xl rounded-2xl shadow-2xl p-8 border border-[color:var(--bg-card-border)] bg-[color:var(--bg-card)]">
          <div className="mb-8 text-center">
            <div className="flex items-center justify-center mb-4">
              <div className="logo-container">
                <img src="/axedras-logo.svg" alt="aXedras Logo" className="h-16 w-auto logo-light" />
                <img src="/axedras-logo-dark.svg" alt="aXedras Logo" className="h-16 w-auto logo-dark" />
              </div>
            </div>
            <h1 className="text-3xl font-bold text-[color:var(--text-primary)] mb-2">{t('auth.login.title')}</h1>
            <p className="text-[color:var(--text-secondary)]">{title}</p>
          </div>

          <div className="flex gap-2 mb-6">
            <button
              type="button"
              className={mode === 'sign_in' ? 'btn flex-1' : 'btn btn-outline flex-1'}
              onClick={() => setMode('sign_in')}
              disabled={isSubmitting}
            >
              {t('auth.login.action')}
            </button>
            <button
              type="button"
              className={mode === 'sign_up' ? 'btn flex-1' : 'btn btn-outline flex-1'}
              onClick={() => setMode('sign_up')}
              disabled={isSubmitting}
            >
              {t('auth.signup.action')}
            </button>
          </div>

          <form
            className="space-y-4"
            onSubmit={e => {
              e.preventDefault()
              void onSubmit()
            }}
          >
            <MessageCenter closeLabel={t('common.action.close')} />

            {mode === 'sign_up' ? (
              <div>
                <label className="block text-sm font-medium text-[color:var(--text-secondary)] mb-1">
                  {t('auth.signup.displayName')}
                </label>
                <input
                  type="text"
                  value={displayName}
                  onChange={e => setDisplayName(e.target.value)}
                  className="w-full rounded-md border border-[color:var(--bg-card-border)] bg-[color:var(--bg-primary)] text-[color:var(--text-primary)] placeholder:text-[color:var(--text-muted)] px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[color:var(--color-gold)] focus:border-[color:var(--color-gold)]"
                  placeholder={t('auth.signup.displayNamePlaceholder')}
                  autoComplete="name"
                  disabled={isSubmitting}
                  required
                />
              </div>
            ) : null}

            <div>
              <label className="block text-sm font-medium text-[color:var(--text-secondary)] mb-1">
                {t('auth.fields.email')}
              </label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="w-full rounded-md border border-[color:var(--bg-card-border)] bg-[color:var(--bg-primary)] text-[color:var(--text-primary)] placeholder:text-[color:var(--text-muted)] px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[color:var(--color-gold)] focus:border-[color:var(--color-gold)]"
                placeholder="you@example.com"
                autoComplete="email"
                disabled={isSubmitting}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-[color:var(--text-secondary)] mb-1">
                {t('auth.fields.password')}
              </label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="w-full rounded-md border border-[color:var(--bg-card-border)] bg-[color:var(--bg-primary)] text-[color:var(--text-primary)] placeholder:text-[color:var(--text-muted)] px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[color:var(--color-gold)] focus:border-[color:var(--color-gold)]"
                placeholder="••••••••"
                autoComplete={mode === 'sign_in' ? 'current-password' : 'new-password'}
                disabled={isSubmitting}
                required
              />
            </div>

            <button type="submit" className="btn w-full" disabled={isSubmitting}>
              {isSubmitting
                ? t('common.status.loading')
                : mode === 'sign_in'
                  ? t('auth.login.action')
                  : t('auth.signup.action')}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
