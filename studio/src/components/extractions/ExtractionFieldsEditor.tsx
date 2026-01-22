import type { ExtractionCorrectionInput } from '../../services/core/extraction/types'

export type ExtractionFieldsEditorProps = {
  form: ExtractionCorrectionInput
  disabled: boolean
  saving: boolean
  t: (key: string) => string
  onChange: (key: keyof ExtractionCorrectionInput, value: string) => void
}

export function ExtractionFieldsEditor(props: ExtractionFieldsEditorProps) {
  const { form, disabled, saving, t, onChange } = props

  return (
    <>
      <h3 className="text-body font-bold mb-4">{t('extraction.detail.fields')}</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <label className="block">
          <div className="text-label mb-1">{t('common.fields.serialNumber')}</div>
          <input
            className="input"
            value={form.serial_number ?? ''}
            onChange={e => onChange('serial_number', e.target.value)}
            disabled={disabled || saving}
          />
        </label>

        <label className="block">
          <div className="text-label mb-1">{t('common.fields.metal')}</div>
          <input
            className="input"
            value={form.metal ?? ''}
            onChange={e => onChange('metal', e.target.value)}
            disabled={disabled || saving}
          />
        </label>

        <label className="block">
          <div className="text-label mb-1">{t('common.fields.weight')}</div>
          <input
            className="input"
            value={form.weight ?? ''}
            onChange={e => onChange('weight', e.target.value)}
            disabled={disabled || saving}
          />
        </label>

        <label className="block">
          <div className="text-label mb-1">{t('extraction.fields.weightUnit')}</div>
          <input
            className="input"
            value={form.weight_unit ?? ''}
            onChange={e => onChange('weight_unit', e.target.value)}
            disabled={disabled || saving}
          />
        </label>

        <label className="block">
          <div className="text-label mb-1">{t('common.fields.purity')}</div>
          <input
            className="input"
            value={form.fineness ?? ''}
            onChange={e => onChange('fineness', e.target.value)}
            disabled={disabled || saving}
          />
        </label>

        <label className="block">
          <div className="text-label mb-1">{t('common.fields.manufacturer')}</div>
          <input
            className="input"
            value={form.producer ?? ''}
            onChange={e => onChange('producer', e.target.value)}
            disabled={disabled || saving}
          />
        </label>
      </div>
    </>
  )
}
