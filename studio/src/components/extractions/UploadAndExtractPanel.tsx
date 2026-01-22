import { useCallback, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { services } from '../../services'
import type { StrategyChoice } from '../../services/core/extraction/types'
import { useAppTranslation, I18N_SCOPES } from '../../lib/i18n'
import { InlineSpinner } from '../ui/InlineSpinner'
import { ToggleSwitch } from '../ui/ToggleSwitch'
import { useUiMessages } from '../../ui/messages/UiMessagesContext'
import { createErrorMessage } from '../../ui/messages/fromError'

export type UploadAndExtractPanelProps = {
  initialStrategy?: StrategyChoice
  initialUseMockData?: boolean
  initialRegisterOnBil?: boolean
  onAfterExtract?: (payload: { createdOriginalId?: string }) => void
}

export function UploadAndExtractPanel(props: UploadAndExtractPanelProps) {
  const { t } = useAppTranslation(I18N_SCOPES.extraction)
  const { push } = useUiMessages()
  const navigate = useNavigate()

  const { onAfterExtract } = props

  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const [processing, setProcessing] = useState(false)
  const [strategy, setStrategy] = useState<StrategyChoice>(props.initialStrategy ?? 'cloud')
  const [useMockData, setUseMockData] = useState(props.initialUseMockData ?? false)
  const [registerOnBil, setRegisterOnBil] = useState(props.initialRegisterOnBil ?? false)

  const isBusy = processing

  const onPickFile = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const onFileSelected = useCallback(
    async (file: File | null) => {
      if (!file) return

      setProcessing(true)
      try {
        const before = await services.extractionService.listActive()
        const beforeIds = new Set(before.map(r => r.id))

        await services.extractionService.extractFromUpload({
          file,
          strategy,
          useMock: useMockData,
          registerOnBil,
        })

        // The server awaits persistence before returning, so the row should exist now.
        const after = await services.extractionService.listActive()
        const created = after.find(r => !beforeIds.has(r.id))

        push({
          variant: 'success',
          title: t('common.toast.upload.title'),
          description: t('common.toast.upload.description'),
        })

        const createdOriginalId = created?.original_id

        onAfterExtract?.({ createdOriginalId })

        if (onAfterExtract) return

        if (createdOriginalId) {
          navigate(`/extractions/${createdOriginalId}`)
          return
        }

        navigate('/extractions')
      } catch (error) {
        push(createErrorMessage(t, error))
      } finally {
        setProcessing(false)
      }
    },
    [navigate, onAfterExtract, push, registerOnBil, strategy, t, useMockData]
  )

  return (
    <div className="panel">
      <div className="flex items-center gap-4 mb-6">
        <div className="w-12 h-12 bg-gradient-to-br from-yellow-500 to-orange-500 rounded-full flex items-center justify-center flex-shrink-0 shadow-lg">
          <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
            />
          </svg>
        </div>
        <div>
          <h3 className="text-body font-bold mb-1">{t('extraction.upload.title')}</h3>
          <p className="text-label">{t('extraction.upload.description')}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3">
        <div>
          <div className="text-label mb-1">{t('extraction.upload.aiStrategy')}</div>
          <div className="inline-flex rounded-md border border-[color:var(--bg-card-border)] overflow-hidden">
            <button
              type="button"
              className={`px-3 py-2 text-sm font-medium transition-colors ${
                strategy === 'cloud'
                  ? 'bg-[color:var(--color-gold)] text-white'
                  : 'bg-transparent text-[color:var(--text-primary)]'
              }`}
              onClick={() => setStrategy('cloud')}
              disabled={isBusy}
            >
              {t('extraction.upload.strategyCloud')}
            </button>
            <button
              type="button"
              className={`px-3 py-2 text-sm font-medium transition-colors border-l border-[color:var(--bg-card-border)] ${
                strategy === 'local'
                  ? 'bg-[color:var(--color-gold)] text-white'
                  : 'bg-transparent text-[color:var(--text-primary)]'
              }`}
              onClick={() => setStrategy('local')}
              disabled={isBusy}
            >
              {t('extraction.upload.strategyLocal')}
            </button>
          </div>
        </div>

        <ToggleSwitch
          checked={useMockData}
          onChange={setUseMockData}
          disabled={isBusy}
          label={t('extraction.upload.useMock')}
        />

        <ToggleSwitch
          checked={registerOnBil}
          onChange={setRegisterOnBil}
          disabled={isBusy}
          label={t('extraction.upload.registerOnBil')}
        />

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={e => {
            const file = e.target.files?.[0] ?? null
            // reset so selecting the same file twice triggers change
            e.target.value = ''
            void onFileSelected(file)
          }}
        />

        <button className="btn w-full" onClick={onPickFile} disabled={isBusy}>
          {isBusy ? (
            <>
              <InlineSpinner />
              {t('common.status.uploading')}
            </>
          ) : (
            t('extraction.upload.action')
          )}
        </button>

        {isBusy ? (
          <div className="mt-3 flex items-center gap-2 text-sm text-[color:var(--text-secondary)]">
            <InlineSpinner size={16} />
            {t('extraction.upload.processing')}
          </div>
        ) : null}
      </div>
    </div>
  )
}
