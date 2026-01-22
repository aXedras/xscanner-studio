import { CorrectIcon, RegisterIcon, RejectIcon } from '../ui/ActionIcons'

export type ExtractionDetailActionsProps = {
  disabled: boolean
  saving: boolean
  loading: boolean
  registering: boolean
  rejecting: boolean
  hasActive: boolean
  t: (key: string) => string
  onSave: () => void
  onRegister: () => void
  onReject: () => void
}

export function ExtractionDetailActions(props: ExtractionDetailActionsProps) {
  const { disabled, saving, loading, registering, rejecting, hasActive, t, onSave, onRegister, onReject } = props

  return (
    <div className="flex items-center gap-2">
      <button className="btn" onClick={onSave} disabled={disabled || saving || loading || !hasActive}>
        <span className="inline-flex items-center gap-2">
          <CorrectIcon />
          {saving ? t('common.status.saving') : t('common.action.correct')}
        </span>
      </button>

      <button
        className="btn btn-outline"
        onClick={onRegister}
        disabled={disabled || registering || loading || !hasActive}
        aria-label={t('common.action.register')}
        title={t('common.action.register')}
      >
        <span className="inline-flex items-center gap-2">
          <RegisterIcon />
          {t('common.action.register')}
        </span>
      </button>

      <button
        className="btn btn-outline"
        onClick={onReject}
        disabled={disabled || rejecting || loading || !hasActive}
        aria-label={t('common.action.reject')}
        title={t('common.action.reject')}
      >
        <span className="inline-flex items-center gap-2">
          <RejectIcon />
          {t('common.action.reject')}
        </span>
      </button>
    </div>
  )
}
